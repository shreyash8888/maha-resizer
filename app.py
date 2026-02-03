from flask import Flask, request, send_file, render_template
from rembg import remove
from PIL import Image
import io

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            try:
                # 1. GET SETTINGS
                doc_type = request.form.get('doc_type')  # 'photo' or 'sign'
                should_remove_bg = 'remove_bg' in request.form 
                
                # --- AUTO-PILOT RULES (No Slider Needed) ---
                if doc_type == 'sign':
                    target_kb = 20  # Strict Rule for Signature
                    target_size = (256, 64)
                else:
                    target_kb = 50  # Strict Rule for Photo
                    target_size = (160, 200)

                # 2. Open & Optimize Input
                input_image = Image.open(file.stream)
                input_image.thumbnail((1000, 1000)) # Speed Hack

                # 3. AI Background Removal (Only if requested)
                if should_remove_bg:
                    img_byte_arr = io.BytesIO()
                    input_image.save(img_byte_arr, format='PNG')
                    output_bytes = remove(img_byte_arr.getvalue())
                    
                    img_no_bg = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
                    processed_image = Image.new("RGBA", img_no_bg.size, "WHITE")
                    processed_image.paste(img_no_bg, (0, 0), img_no_bg)
                    processed_image = processed_image.convert("RGB")
                else:
                    processed_image = input_image.convert("RGB")

                # 4. Resize Dimensions
                processed_image = processed_image.resize(target_size)

                # 5. Compress to Target KB (Smart Loop)
                output_io = io.BytesIO()
                quality = 100
                step = 5
                
                # Initial save
                processed_image.save(output_io, 'JPEG', quality=quality)
                
                # Reduce quality until it fits the strict limit
                while output_io.tell() > (target_kb * 1024) and quality > 10:
                    output_io = io.BytesIO()
                    quality -= step
                    processed_image.save(output_io, 'JPEG', quality=quality)

                output_io.seek(0)
                
                filename = f"mpsc_{doc_type}_optimized.jpg"
                return send_file(output_io, mimetype='image/jpeg', as_attachment=True, download_name=filename)
            
            except Exception as e:
                return f"Error: {str(e)}"

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)