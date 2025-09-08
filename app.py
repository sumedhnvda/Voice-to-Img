import streamlit as st
from utils import transcribe_audio, split_into_scenes, call_banana_api
import time

st.set_page_config(page_title="Voice to Image Generator", layout="wide")
st.title("🎙️ Voice to Image Generator")

mode = st.radio("Choose Mode", ["Single Image", "Dream Sequence"])

uploaded_audio = st.file_uploader("Record or upload your dream description", type=["wav", "mp3", "m4a"])

if st.button("Transform Dream to Images") and uploaded_audio is not None:
    audio_bytes = uploaded_audio.read()
    st.info("🎧 Transcribing your dream description...")
    try:
        text = transcribe_audio(audio_bytes, uploaded_audio.name)
        st.success("✨ Dream captured successfully!")
        st.markdown("### 📝 Your Dream Description:")
        st.write(text)
    except Exception as e:
        st.error(f"Error during transcription: {e}")
        st.stop()

    context_bytes = None 

    if mode == "Single Image":
        st.info("Generating image...")
        result = call_banana_api(text, context_bytes)
        
        if isinstance(result, dict) and "error" in result:
            st.error(f"Image generation failed: {result['error']}")
        elif isinstance(result, list) and len(result) > 0:
            try:
                img_base64 = result[0].get("image", "")
                if img_base64:
                    import base64
                    image_bytes = base64.b64decode(img_base64)
                    st.image(image_bytes, caption="Generated Image")
                else:
                    st.error("No image data in the response")
            except Exception as e:
                st.error(f"Error processing image: {str(e)}")
        else:
            st.error("Unexpected response format from the API")

    else:  
        st.info("Splitting text into scenes...")
        try:
            scenes = split_into_scenes(text)
            if not scenes:
                st.error("No scenes were identified. Please try with a longer or more detailed description.")
                st.stop()
                
            st.success(f"Successfully identified {len(scenes)} scenes!")
            scenes_container = st.container()
            with scenes_container:
                for idx, scene in enumerate(scenes, 1):
                    st.write(f"🎬 {scene}")
            
            st.info("Generating images for each scene...")
            image_cols = st.columns(min(3, len(scenes)))  
            
            for idx, scene in enumerate(scenes, 1):
                col_idx = (idx - 1) % len(image_cols)
                with image_cols[col_idx]:
                    st.write(f"🎨 Generating Scene {idx}...")
                
                    if idx > 1:
                        time.sleep(2)
    
                    for attempt in range(3):
                        result = call_banana_api(scene, context_bytes)
                        
                        if isinstance(result, dict) and "error" in result:
                            error_msg = result['error']
                            if attempt < 2:  
                                st.warning(f"Attempt {attempt + 1} failed: {error_msg}. Retrying...")
                                time.sleep(2)  
                                continue
                            else:
                                st.error(f"Failed after all attempts: {error_msg}")
                        elif isinstance(result, list) and len(result) > 0:
                            try:
                                img_base64 = result[0].get("image", "")
                                if img_base64:
                                    import base64
                                    image_bytes = base64.b64decode(img_base64)
                                    st.image(image_bytes, caption=f"✨ Dream Scene {idx}")
                                    break  
                                else:
                                    if attempt < 2:
                                        st.warning(f"Attempt {attempt + 1}: No image data. Retrying...")
                                        time.sleep(2)
                                        continue
                                    else:
                                        st.error("No image generated after all attempts")
                            except Exception as e:
                                if attempt < 2:
                                    st.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying...")
                                    time.sleep(2)
                                    continue
                                else:
                                    st.error(f"Error processing image: {str(e)}")
                        else:
                            if attempt < 2:
                                st.warning(f"Attempt {attempt + 1}: Unexpected response. Retrying...")
                                time.sleep(2)
                                continue
                            else:
                                st.error("Unexpected API response after all attempts")
                        
        except Exception as e:
            st.error(f"Error processing scenes: {str(e)}")
            st.stop()
            result = call_banana_api(scene, context_bytes)
            
            if isinstance(result, dict) and "error" in result:
                st.error(f"Image generation failed for Scene {idx}: {result['error']}")
            elif isinstance(result, list) and len(result) > 0:
                try:
                    img_base64 = result[0].get("image", "")
                    if img_base64:
                        import base64
                        image_bytes = base64.b64decode(img_base64)
                        st.image(image_bytes, caption=f"Scene {idx}")
                    else:
                        st.error(f"No image data in response for Scene {idx}")
                except Exception as e:
                    st.error(f"Error processing image for Scene {idx}: {str(e)}")
            else:
                st.error(f"Unexpected response format from API for Scene {idx}")
