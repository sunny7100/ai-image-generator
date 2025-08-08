import streamlit as st
import requests
from PIL import Image, ImageDraw, ImageFont
import io
import time
import os

# Configure page
st.set_page_config(
    page_title="AI Image Generator",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #ff6b6b, #4ecdc4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        border: none;
        padding: 0.5rem 1rem;
        font-size: 1.1rem;
        font-weight: bold;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #28a745;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

def generate_image_api(prompt, negative_prompt=""):
    """Generate image using Hugging Face API with authentication token"""
    try:
        API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
        hf_api_token = os.getenv("HUGGINGFACE_API_TOKEN", None)
        if not hf_api_token:
            return None, "Missing Hugging Face API token. Set HUGGINGFACE_API_TOKEN environment variable."

        headers = {
            "Authorization": f"Bearer {hf_api_token}",
            "Content-Type": "application/json"
        }

        prompt_text = prompt
        if negative_prompt:
            prompt_text += f". Negative: {negative_prompt}"

        payload = {
            "inputs": prompt_text
        }

        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)

        if response.status_code == 200:
            image_bytes = response.content
            image = Image.open(io.BytesIO(image_bytes))
            return image, None
        else:
            return None, f"API Error: {response.status_code} - {response.text}"

    except requests.exceptions.Timeout:
        return None, "Request timed out. The service might be busy. Please try again."
    except Exception as e:
        return None, f"Error generating image: {str(e)}"

def generate_placeholder_image(prompt):
    """Generate a placeholder image when API fails"""
    try:
        img = Image.new('RGB', (512, 512), color='lightblue')
        draw = ImageDraw.Draw(img)

        text = f"Generated for:\n{prompt[:50]}..."
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None

        bbox = draw.textbbox((0, 0), text, font=font) if font else (0, 0, 200, 40)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (512 - text_width) // 2
        y = (512 - text_height) // 2

        draw.text((x, y), text, fill='darkblue', font=font)

        return img
    except Exception:
        return Image.new('RGB', (512, 512), color='lightgray')

def save_image(image, filename):
    """Save image to bytes for download"""
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

def main():
    st.markdown('<h1 class="main-header">🎨 AI Image Generator</h1>', unsafe_allow_html=True)
    st.markdown("### Generate stunning images from text descriptions using AI")

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("**Created by:** Your Name | **Tech Stack:** Python, Streamlit, Hugging Face API")
    st.markdown("---")

    if 'generated_image' not in st.session_state:
        st.session_state.generated_image = None
    if 'generation_time' not in st.session_state:
        st.session_state.generation_time = 0
    if 'last_prompt' not in st.session_state:
        st.session_state.last_prompt = ""

    with st.sidebar:
        st.header("🛠️ Generation Settings")
        generation_mode = st.radio(
            "Generation Mode:",
            ["🌐 Online API (Recommended)", "🎨 Demo Mode (Fallback)"],
            help="Online API uses real AI models. Demo mode creates placeholder images."
        )
        st.header("💡 Example Prompts")
        example_prompts = [
            "A serene mountain landscape at sunset",
            "A futuristic robot in a cyberpunk city",
            "A cute cat wearing sunglasses",
            "Abstract art with vibrant colors",
            "A magical forest with glowing mushrooms",
            "A modern city skyline at night",
            "A peaceful garden with butterflies",
            "A vintage car on a country road"
        ]
        selected_example = st.selectbox("Choose an example:", [""] + example_prompts)
        if st.button("Use Selected Example") and selected_example:
            st.session_state.selected_prompt = selected_example

    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("📝 Describe Your Image")
        default_prompt = st.session_state.get('selected_prompt', '')
        prompt = st.text_area(
            "Enter your prompt:",
            value=default_prompt,
            height=120,
            placeholder="Describe the image you want to generate...",
            key="prompt_input"
        )
        negative_prompt = st.text_area(
            "Negative prompt (optional):",
            height=80,
            placeholder="What you don't want (e.g., blurry, low quality)",
            value="blurry, low quality, distorted"
        )
        generate_btn = st.button("🚀 Generate Image", type="primary", use_container_width=True)

        if generation_mode == "🎨 Demo Mode (Fallback)":
            st.info("💡 Demo mode will create a placeholder image with your prompt text. Use Online API mode for real AI generation.")
        else:
            st.info("💡 Using free Hugging Face API. First generation may take 20-30 seconds as the model loads.")

    with col2:
        st.header("🖼️ Generated Image")
        image_container = st.container()
        if st.session_state.generated_image is None:
            with image_container:
                st.info("👆 Enter a prompt and click 'Generate Image' to create your artwork!")

    if generate_btn and prompt.strip():
        with st.spinner("🎨 Creating your masterpiece... Please wait..."):
            start_time = time.time()
            try:
                if generation_mode == "🌐 Online API (Recommended)":
                    generated_image, error = generate_image_api(prompt, negative_prompt)
                    if generated_image is not None:
                        st.session_state.generated_image = generated_image
                        st.session_state.generation_time = time.time() - start_time
                        st.session_state.last_prompt = prompt

                        with image_container:
                            st.image(generated_image, caption=f"Generated in {st.session_state.generation_time:.2f} seconds", use_container_width=True)
                            st.markdown(f'<div class="success-message">✅ Image generated successfully!</div>', unsafe_allow_html=True)

                            img_bytes = save_image(generated_image, "generated_image.png")
                            st.download_button(
                                label="📥 Download High Quality PNG",
                                data=img_bytes,
                                file_name=f"ai_generated_{int(time.time())}.png",
                                mime="image/png",
                                use_container_width=True
                            )
                    else:
                        st.markdown(f'<div class="error-message">❌ API Generation Failed: {error}</div>', unsafe_allow_html=True)
                        st.info("🔄 Falling back to demo mode...")

                        placeholder_image = generate_placeholder_image(prompt)
                        st.session_state.generated_image = placeholder_image
                        st.session_state.generation_time = time.time() - start_time
                        st.session_state.last_prompt = prompt

                        with image_container:
                            st.image(placeholder_image, caption="Demo placeholder image", use_container_width=True)
                            st.warning("This is a placeholder image. Try again later when the API service is available.")
                else:
                    placeholder_image = generate_placeholder_image(prompt)
                    st.session_state.generated_image = placeholder_image
                    st.session_state.generation_time = time.time() - start_time
                    st.session_state.last_prompt = prompt

                    with image_container:
                        st.image(placeholder_image, caption="Demo placeholder image", use_container_width=True)
                        st.info("📋 This is demo mode. Switch to 'Online API' mode for real AI generation.")

                        img_bytes = save_image(placeholder_image, "demo_image.png")
                        st.download_button(
                            label="📥 Download Demo Image",
                            data=img_bytes,
                            file_name=f"demo_{int(time.time())}.png",
                            mime="image/png",
                            use_container_width=True
                        )

            except Exception as e:
                st.markdown(f'<div class="error-message">❌ Unexpected Error: {str(e)}</div>', unsafe_allow_html=True)
                st.info("💡 Try refreshing the page or using demo mode.")
    elif generate_btn and not prompt.strip():
        st.warning("⚠️ Please enter a prompt to generate an image!")

    if st.session_state.generated_image is not None and not generate_btn:
        with image_container:
            st.image(st.session_state.generated_image,
                     caption=f"Last generated image (took {st.session_state.generation_time:.2f} seconds)",
                     use_container_width=True)

            img_bytes = save_image(st.session_state.generated_image, "generated_image.png")
            st.download_button(
                label="📥 Download This Image",
                data=img_bytes,
                file_name=f"ai_generated_{int(time.time())}.png",
                mime="image/png",
                use_container_width=True
            )

            if st.session_state.last_prompt:
                with st.expander("📋 Prompt Used"):
                    st.code(st.session_state.last_prompt, language="text")

    st.markdown("---")
    with st.expander("ℹ️ About this App & Troubleshooting"):
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("""
            **About this App:**
            - Uses Hugging Face API for real AI generation (requires token)
            - Built with Python & Streamlit
            - Fallback demo mode when API is busy or token missing
            - Free and open source

            **If generation fails:**
            - Try demo mode first
            - Wait a few minutes and retry
            - Check your internet connection
            - Refresh the page if needed
            """)
        with col2:
            st.markdown("""
            **Tips for better results:**
            - Be specific and descriptive
            - Add art styles (e.g., "photorealistic", "oil painting")
            - Specify lighting and mood
            - Keep prompts under 100 words

            **Common issues:**
            - First generation takes longer (model loading)
            - API might be busy during peak times
            - Some prompts may be filtered for content
            """)

    st.sidebar.markdown("---")
    st.sidebar.markdown("**💻 System Status**")
    st.sidebar.success("✅ App Running")
    if generation_mode == "🌐 Online API (Recommended)":
        st.sidebar.info("🌐 Using Hugging Face API")
    else:
        st.sidebar.info("🎨 Demo Mode Active")

    st.sidebar.markdown("---")
    st.sidebar.markdown("**🔗 Connect with Me**")
    st.sidebar.markdown("[![GitHub](https://img.shields.io/badge/GitHub-000000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/yourusername)")
    st.sidebar.markdown("[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/yourusername)")

if __name__ == "__main__":
    main()
