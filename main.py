from fastapi import FastAPI, HTTPException
import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain.prompts import PromptTemplate
from pydantic import BaseModel
# from contextlib import asynccontextmanager
# import cv2
import cloudinary.uploader
# from diffusers import StableDiffusionPipeline
from app.function import load_llm, get_src_original_url
from supabase import create_client, Client


cloudinary.config(
    cloud_name="dtuqpup4a",  # replace with your Cloudinary cloud name
    api_key="291317165429892",  # replace with your Cloudinary API key
    api_secret="qJq00V57nGffgM_ev-BcG5Tbmnk"  # replace with your Cloudinary API secret
)

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     global image_pipe
#     image_pipe = StableDiffusionPipeline.from_pretrained("CompVis/stable-diffusion-v1-4")

#     # Yield control back to FastAPI
#     yield

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
supabase: Client = create_client('https://hwhwcqocrdidmwixrlil.supabase.co', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh3aHdjcW9jcmRpZG13aXhybGlsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjU5ODc1OTMsImV4cCI6MjA0MTU2MzU5M30.ZvoeulclLUddd92a9tdvUb905dEvLoiFqRafEEpibZk')

class BlogInput(BaseModel):
    blog_input: str
    image_input: str

class AdvertisementRequest(BaseModel):
    product_name: str
    background_description: str
    
class AuthInput(BaseModel):
    email: str
    password: str

@app.post("/register")
def register(auth_input: AuthInput):
    try:
        response = supabase.auth.sign_up({
            "email": auth_input.email,
            "password": auth_input.password,
        })
        return {"message": "User registered successfully!", "user_id": response.user.id}
    except Exception as e:
        logging.error(f"Registration error: {e}")
        raise HTTPException(status_code=400, detail="Registration failed")

@app.post("/login")
def login(auth_input: AuthInput):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": auth_input.email,
            "password": auth_input.password,
        })
        return {"message": "Login successful!", "access_token": response.session.access_token}
    except Exception as e:
        logging.error(f"Login error: {e}")
        raise HTTPException(status_code=401, detail="Login failed")

# @app.post("/generate_advertisement")
# async def generate_advertisement(request: AdvertisementRequest):
#     try:
#         # Extract product_name and background_description from request body
#         product_name = request.product_name
#         background_description = request.background_description
#         logger.info(f"Received request to generate advertisement for product: {product_name}")

#         # Image prompts with dynamic product name and background
#         image_prompts = [
#             f"A {product_name} bottle emerging from a foggy background {background_description} and dramatic lighting with a rotating effect.",
#             f"Close-up of the {product_name} bottle rotating to highlight its features {background_description} with soft, elegant lighting.",
#             f"A person in a stylish setting applying the {product_name} {background_description}, showing satisfaction.",
#             f"Animated visual effect representing the {product_name} mist spreading around the scene {background_description}.",
#             f"The {product_name} bottle fading out {background_description}."
#         ]

#         logger.info(f"Generated image prompts: {image_prompts}")

#         # Generate images based on prompts
#         image_filenames = []
#         for i, prompt in enumerate(image_prompts):
#             logger.info(f"Generating image for prompt {i + 1}/{len(image_prompts)}: {prompt}")
#             image = image_pipe(prompt).images[0]
#             image_filename = f"frame_{i}.png"
#             image.save(image_filename)
#             image_filenames.append(image_filename)
#             logger.info(f"Saved image: {image_filename}")

#         # Create video from images
#         frame_rate = 2
#         video_filename = "advertisement.mp4"

#         first_image = cv2.imread(image_filenames[0])
#         frame_size = (first_image.shape[1], first_image.shape[0])

#         logger.info("Creating video from generated images.")
#         fourcc = cv2.VideoWriter_fourcc(*'avc1')  # Correct fourcc for H.264 codec
#         video_writer = cv2.VideoWriter(video_filename, fourcc, frame_rate, frame_size)

#         for image_filename in image_filenames:
#             frame = cv2.imread(image_filename)
#             video_writer.write(frame)
#             logger.info(f"Added frame to video: {image_filename}")

#         video_writer.release()
#         logger.info(f"Video created successfully: {video_filename}")

#         # Upload video to Cloudinary
#         logger.info("Uploading video to Cloudinary.")
#         cloudinary_result = cloudinary.uploader.upload_large(
#             video_filename, resource_type="video"
#         )
#         logger.info(f"Cloudinary upload response: {cloudinary_result}")  # Added logging
#         cloudinary_url = cloudinary_result['secure_url']
#         logger.info(f"Video uploaded successfully. URL: {cloudinary_url}")


#         # Return the Cloudinary URL in the response
#         return JSONResponse(content={"video_url": cloudinary_url})

#     except Exception as e:
#         logger.error(f"Error occurred while generating advertisement: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))


# API endpoint to generate the blog content and return the image and content
@app.post("/generate_blog")
def generate_blog(request_body: BlogInput):
    blog_input = request_body.blog_input
    image_input = request_body.image_input

    # Fetch the image and its description
    logging.info(f"Route has received the data: {blog_input} & {image_input}")
    image_url, image_description = get_src_original_url(image_input)
    
    # Generate blog content based on the image description
    prompt_template_str = (
        "You are a digital marketing and SEO expert. Write a blog post inspired by the following description: "
        "{blog_description}. The blog should be around 500 words long, and it should be informative and engaging."
    )

    prompt_template = PromptTemplate.from_template(prompt_template_str)
    llm = load_llm(max_tokens=600)
    
    # Chain the prompt template with the LLM
    sequence = prompt_template | llm
    
    # Generate the blog content by passing the input to the chain
    result = sequence.invoke(input={"blog_description": blog_input})
    
    # Check if result is a string or dictionary
    if isinstance(result, str):
        blog_content = result
    else:
        blog_content = result.get('text', '')

    if blog_content:
        return JSONResponse(content={
            "blog_content": blog_content,
            "image": image_url,
            "image_alt": image_description,
        })
    else:
        raise HTTPException(status_code=500, detail="Your article couldn't be generated!")