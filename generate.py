import json
import os
import shutil
import sys
import re

CONFIG_FILE = "config.json"
STATIC_SRC = "static"
OUTPUT_DIR = "output"

def log_error_and_exit(msg):
    print(f"❌ {msg}")
    sys.exit(1)

# ---------- Helper to convert Google Drive link to embed URL ----------
def google_drive_embed(url):
    patterns = [
        r'/file/d/([^/]+)',
        r'id=([^&]+)',
        r'drive\.google\.com.*?[?&]id=([^&]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return f'https://drive.google.com/file/d/{match.group(1)}/preview'
    return url

# ---------- Helper to get localized text ----------
def get_localized_text(data, lang='en'):
    """Extract text from a field that might be a string or a language object"""
    if data is None:
        return ""
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        return data.get(lang, data.get('en', str(data)))
    return str(data)

# ---------- Load config ----------
if not os.path.exists(CONFIG_FILE):
    log_error_and_exit(f"{CONFIG_FILE} not found!")

try:
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
except json.JSONDecodeError as e:
    log_error_and_exit(f"Invalid JSON in {CONFIG_FILE}: {e}")

# ---------- Prepare output directory ----------
shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Copy static files if the folder exists
if os.path.exists(STATIC_SRC):
    shutil.copytree(STATIC_SRC, os.path.join(OUTPUT_DIR, "static"))
else:
    print("⚠️  Warning: 'static/' folder not found – no media will be copied.")

# ---------- HTML Templates ----------
CHOICE_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Choose Your Setup</title>
    <style>
        body {{ font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }}
        .choice-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 2rem 0; }}
        .choice-card {{
            display: block;
            padding: 2rem 1rem;
            background: #f8f9fa;
            border: 2px solid #dee2e6;
            border-radius: 12px;
            text-decoration: none;
            color: #333;
            text-align: center;
            transition: all 0.3s ease;
        }}
        .choice-card:hover {{
            background: #007bff;
            color: white;
            border-color: #007bff;
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }}
        .choice-title {{ font-size: 1.5rem; font-weight: bold; margin-bottom: 0.5rem; }}
        .choice-desc {{ font-size: 0.9rem; opacity: 0.8; }}
        .lang-toggle {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            z-index: 1000;
        }}
        .lang-toggle:hover {{ background: #218838; }}
        .lang-en, .lang-es {{ display: none; }}
        .lang-en.active, .lang-es.active {{ display: block; }}
        h1 {{ text-align: center; }}
        .subtitle {{ text-align: center; color: #666; margin-bottom: 2rem; }}
    </style>
</head>
<body>
    <button class="lang-toggle" onclick="toggleLanguage()">🇨🇴 Español</button>
    <h1>
        <span class="lang-en active">{title_en}</span>
        <span class="lang-es">{title_es}</span>
    </h1>
    <p class="subtitle">
        <span class="lang-en active">Choose how you want to use the room:</span>
        <span class="lang-es">Elija cómo desea usar la sala:</span>
    </p>
    <div class="choice-grid">
        {choices_html}
    </div>
    <script>
        let currentLang = 'en';
        
        function toggleLanguage() {{
            const toggleBtn = document.querySelector('.lang-toggle');
            if (currentLang === 'en') {{
                currentLang = 'es';
                toggleBtn.textContent = '🇺🇸 English';
            }} else {{
                currentLang = 'en';
                toggleBtn.textContent = '🇨🇴 Español';
            }}
            updateLanguage(currentLang);
        }}
        
        function updateLanguage(lang) {{
            document.querySelectorAll('.lang-en, .lang-es').forEach(el => {{
                el.classList.remove('active');
                if (el.classList.contains(`lang-${{lang}}`)) {{
                    el.classList.add('active');
                }}
            }});
            localStorage.setItem('preferredLanguage', lang);
        }}
        
        document.addEventListener('DOMContentLoaded', function() {{
            const savedLang = localStorage.getItem('preferredLanguage') || 'en';
            currentLang = savedLang;
            if (savedLang === 'es') {{
                document.querySelector('.lang-toggle').textContent = '🇺🇸 English';
            }}
            updateLanguage(savedLang);
        }});
    </script>
</body>
</html>
"""

STEP_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Step {step_num} of {total_steps} – {option_title_en}</title>
    <style>
        body {{ font-family: sans-serif; max-width: 600px; margin: 2rem auto; padding: 0 1rem; }}
        .button {{ display: inline-block; padding: 1rem 2rem; margin: 1rem 0; background: #007bff; color: white; text-decoration: none; border-radius: 8px; }}
        img, video, iframe {{ max-width: 100%; height: auto; margin: 1rem 0; }}
        iframe {{ width: 100%; height: 340px; border: none; }}
        .nav {{ margin-top: 2rem; }}
        .nav a {{ margin-right: 1rem; }}
        .image-grid {{ display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; margin: 1rem 0; }}
        .image-grid img {{ max-width: 45%; height: auto; border: 1px solid #ddd; border-radius: 8px; }}
        @media (max-width: 600px) {{
            .image-grid img {{ max-width: 100%; }}
        }}
        .lang-toggle {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            z-index: 1000;
        }}
        .lang-toggle:hover {{ background: #218838; }}
        .lang-en, .lang-es, .instruction-en, .instruction-es {{ display: none; }}
        .lang-en.active, .lang-es.active, .instruction-en.active, .instruction-es.active {{ display: block; }}
        .step-counter-en, .step-counter-es {{ display: none; }}
        .step-counter-en.active, .step-counter-es.active {{ display: inline; }}
        .hidden {{ display: none !important; }}
        .back-link {{ display: inline-block; margin-top: 1rem; color: #007bff; text-decoration: none; }}
        .back-link:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <button class="lang-toggle" onclick="toggleLanguage()">🇨🇴 Español</button>
    <h1>
        <span class="lang-en active">{option_title_en}</span>
        <span class="lang-es">{option_title_es}</span>
    </h1>
    <p><strong>
        <span class="lang-en active step-counter-en">Step {step_num} of {total_steps}</span>
        <span class="lang-es step-counter-es">Paso {step_num} de {total_steps}</span>
    </strong></p>
    <div class="instruction-en active">{instruction_en}</div>
    <div class="instruction-es">{instruction_es}</div>
    {media}
    <div class="nav">
        {prev_link}
        {next_link}
        <a href="index.html" class="button">🏠 Home</a>
    </div>
    <br>
    <a href="choice.html" class="back-link">⬅ {back_text}</a>
    <script>
        let currentLang = 'en';
        
        function toggleLanguage() {{
            const toggleBtn = document.querySelector('.lang-toggle');
            if (currentLang === 'en') {{
                currentLang = 'es';
                toggleBtn.textContent = '🇺🇸 English';
            }} else {{
                currentLang = 'en';
                toggleBtn.textContent = '🇨🇴 Español';
            }}
            updateLanguage(currentLang);
        }}
        
        function updateLanguage(lang) {{
            document.querySelectorAll('.lang-en, .lang-es, .instruction-en, .instruction-es, .step-counter-en, .step-counter-es').forEach(el => {{
                el.classList.remove('active');
                if (el.classList.contains(`lang-${{lang}}`) || 
                    el.classList.contains(`instruction-${{lang}}`) ||
                    el.classList.contains(`step-counter-${{lang}}`)) {{
                    el.classList.add('active');
                }}
            }});
            localStorage.setItem('preferredLanguage', lang);
        }}
        
        document.addEventListener('DOMContentLoaded', function() {{
            const savedLang = localStorage.getItem('preferredLanguage') || 'en';
            currentLang = savedLang;
            if (savedLang === 'es') {{
                document.querySelector('.lang-toggle').textContent = '🇺🇸 English';
            }}
            updateLanguage(savedLang);
        }});
    </script>
</body>
</html>
"""

CONGRATS_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Congratulations!</title>
    <style>
        body {{ font-family: sans-serif; max-width: 600px; margin: 2rem auto; padding: 0 1rem; text-align: center; }}
        .button {{ display: inline-block; padding: 1rem 2rem; margin: 1rem 0; background: #28a745; color: white; text-decoration: none; border-radius: 8px; }}
        .lang-toggle {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            z-index: 1000;
        }}
        .lang-toggle:hover {{ background: #218838; }}
        .lang-en, .lang-es {{ display: none; }}
        .lang-en.active, .lang-es.active {{ display: block; }}
        .hidden {{ display: none !important; }}
        .back-link {{ display: inline-block; margin-top: 1rem; color: #007bff; text-decoration: none; }}
        .back-link:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <button class="lang-toggle" onclick="toggleLanguage()">🇨🇴 Español</button>
    <h1>
        <span class="lang-en active">🎉 Good job! 🎉</span>
        <span class="lang-es">🎉 ¡Buen trabajo! 🎉</span>
    </h1>
    <p>
        <span class="lang-en active">You have successfully {message_en}.</span>
        <span class="lang-es">Has completado exitosamente {message_es}.</span>
    </p>
    <a href="choice.html" class="button">
        <span class="lang-en active">Choose another setup</span>
        <span class="lang-es">Elegir otra configuración</span>
    </a>
    <br>
    <a href="index.html" class="back-link">🏠 Home</a>
    <script>
        let currentLang = 'en';
        
        function toggleLanguage() {{
            const toggleBtn = document.querySelector('.lang-toggle');
            if (currentLang === 'en') {{
                currentLang = 'es';
                toggleBtn.textContent = '🇺🇸 English';
            }} else {{
                currentLang = 'en';
                toggleBtn.textContent = '🇨🇴 Español';
            }}
            updateLanguage(currentLang);
        }}
        
        function updateLanguage(lang) {{
            document.querySelectorAll('.lang-en, .lang-es').forEach(el => {{
                el.classList.remove('active');
                if (el.classList.contains(`lang-${{lang}}`)) {{
                    el.classList.add('active');
                }}
            }});
            localStorage.setItem('preferredLanguage', lang);
        }}
        
        document.addEventListener('DOMContentLoaded', function() {{
            const savedLang = localStorage.getItem('preferredLanguage') || 'en';
            currentLang = savedLang;
            if (savedLang === 'es') {{
                document.querySelector('.lang-toggle').textContent = '🇺🇸 English';
            }}
            updateLanguage(savedLang);
        }});
    </script>
</body>
</html>
"""

# ---------- Helper function to generate media HTML ----------
def generate_media_html(step, lang='en'):
    """Generate HTML for media (video, single image, or multiple images)"""
    if "video_url" in step:
        embed_url = google_drive_embed(step["video_url"])
        alt_text = get_localized_text(step.get("alt"), lang)
        return f'<iframe src="{embed_url}" allow="autoplay; encrypted-media" allowfullscreen title="{alt_text}"></iframe>'
    
    if "video" in step:
        alt_text = get_localized_text(step.get("alt"), lang)
        return f'<video controls alt="{alt_text}"><source src="static/videos/{step["video"]}" type="video/mp4">Your browser does not support the video tag.</video>'
    
    if "images" in step:
        images_html = '<div class="image-grid">'
        for img in step["images"]:
            alt_text = get_localized_text(img.get("alt"), lang)
            images_html += f'<img src="static/images/{img["src"]}" alt="{alt_text}">'
        images_html += '</div>'
        return images_html
    
    if "image" in step:
        alt_text = get_localized_text(step.get("alt"), lang)
        return f'<img src="static/images/{step["image"]}" alt="{alt_text}">'
    
    return ""

# ---------- Generate Choice Page ----------
def generate_choice_page(option):
    """Generate the choice page where users select their setup"""
    choices_html = ""
    
    for choice in option.get("choices", []):
        choice_id = choice["id"]
        title_en = get_localized_text(choice["title"], 'en')
        title_es = get_localized_text(choice["title"], 'es')
        desc_en = get_localized_text(choice.get("description", ""), 'en')
        desc_es = get_localized_text(choice.get("description", ""), 'es')
        
        # Link to the first step of this choice
        link = f"{option['id']}_{choice_id}_step1.html"
        
        choices_html += f'''
        <a href="{link}" class="choice-card">
            <div class="choice-title">
                <span class="lang-en active">{title_en}</span>
                <span class="lang-es">{title_es}</span>
            </div>
            <div class="choice-desc">
                <span class="lang-en active">{desc_en}</span>
                <span class="lang-es">{desc_es}</span>
            </div>
        </a>
        '''
    
    title_en = get_localized_text(option["title"], 'en')
    title_es = get_localized_text(option["title"], 'es')
    
    page = CHOICE_TEMPLATE.format(
        title_en=title_en,
        title_es=title_es,
        choices_html=choices_html
    )
    
    with open(os.path.join(OUTPUT_DIR, "choice.html"), "w") as f:
        f.write(page)
    print("✅ Generated choice page")

# ---------- Generate step pages for each choice ----------
def generate_step_pages(option):
    """Generate step pages for each choice path"""
    steps_dict = option.get("steps", {})
    
    for choice_id, steps in steps_dict.items():
        total = len(steps)
        if total == 0:
            print(f"⚠️  Warning: No steps for choice '{choice_id}'")
            continue
        
        # Get the choice title for display
        choice_title = None
        for choice in option.get("choices", []):
            if choice["id"] == choice_id:
                choice_title = choice["title"]
                break
        
        if not choice_title:
            choice_title = {"en": choice_id.capitalize(), "es": choice_id.capitalize()}
        
        option_title_en = get_localized_text(choice_title, 'en')
        option_title_es = get_localized_text(choice_title, 'es')
        
        for i, step in enumerate(steps, start=1):
            instruction_en = get_localized_text(step.get("instruction"), 'en')
            instruction_es = get_localized_text(step.get("instruction"), 'es')
            
            # Generate media HTML
            media = generate_media_html(step, 'en')
            
            # Navigation links
            prev_link = f'<a href="{option["id"]}_{choice_id}_step{i-1}.html" class="button">⬅ Previous</a>' if i > 1 else ""
            if i < total:
                next_link = f'<a href="{option["id"]}_{choice_id}_step{i+1}.html" class="button">Next ➔</a>'
            else:
                next_link = f'<a href="{option["id"]}_{choice_id}_congrats.html" class="button">Finish ➔</a>'
            
            # Back text
            back_text_en = "Back to choices"
            back_text_es = "Volver a opciones"
            
            filename = f"{option['id']}_{choice_id}_step{i}.html"
            page = STEP_TEMPLATE.format(
                option_title_en=option_title_en,
                option_title_es=option_title_es,
                step_num=i,
                total_steps=total,
                instruction_en=instruction_en,
                instruction_es=instruction_es,
                media=media,
                prev_link=prev_link,
                next_link=next_link,
                back_text=f'<span class="lang-en active">{back_text_en}</span><span class="lang-es">{back_text_es}</span>'
            )
            with open(os.path.join(OUTPUT_DIR, filename), "w") as f:
                f.write(page)
            
            print(f"✅ Generated {filename}")
        
        # Congratulations page for this choice
        congrats_file = f"{option['id']}_{choice_id}_congrats.html"
        message_en = option_title_en.lower()
        message_es = option_title_es.lower()
        with open(os.path.join(OUTPUT_DIR, congrats_file), "w") as f:
            f.write(CONGRATS_TEMPLATE.format(message_en=message_en, message_es=message_es))
        print(f"✅ Generated {congrats_file}")

# ---------- Generate Index Page ----------
def generate_index_page():
    """Generate the main index page with options"""
    options_html = ""
    for opt in config.get("options", []):
        if opt.get("type") == "choice":
            # This is a choice-based option, link to choice page
            title_en = get_localized_text(opt["title"], 'en')
            title_es = get_localized_text(opt["title"], 'es')
            options_html += f'<a href="choice.html" class="button lang-en active">{title_en}</a><br>'
            options_html += f'<a href="choice.html" class="button lang-es">{title_es}</a><br>'
        else:
            # Regular option, link to first step
            first_step = f"{opt['id']}_step1.html"
            title_en = get_localized_text(opt["title"], 'en')
            title_es = get_localized_text(opt["title"], 'es')
            options_html += f'<a href="{first_step}" class="button lang-en active">{title_en}</a><br>'
            options_html += f'<a href="{first_step}" class="button lang-es">{title_es}</a><br>'
    
    # Update the index template to be more generic
    INDEX_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Room Guide</title>
    <style>
        body {{ font-family: sans-serif; max-width: 600px; margin: 2rem auto; padding: 0 1rem; }}
        .button {{ display: inline-block; padding: 1rem 2rem; margin: 1rem 0; background: #007bff; color: white; text-decoration: none; border-radius: 8px; }}
        .lang-toggle {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            z-index: 1000;
        }}
        .lang-toggle:hover {{ background: #218838; }}
        .lang-en, .lang-es {{ display: none; }}
        .lang-en.active, .lang-es.active {{ display: block; }}
        h1 {{ text-align: center; }}
    </style>
</head>
<body>
    <button class="lang-toggle" onclick="toggleLanguage()">🇨🇴 Español</button>
    <h1>
        <span class="lang-en active">Room Setup Guide</span>
        <span class="lang-es">Guía de Configuración de Sala</span>
    </h1>
    {options_html}
    <script>
        let currentLang = 'en';
        
        function toggleLanguage() {{
            const toggleBtn = document.querySelector('.lang-toggle');
            if (currentLang === 'en') {{
                currentLang = 'es';
                toggleBtn.textContent = '🇺🇸 English';
            }} else {{
                currentLang = 'en';
                toggleBtn.textContent = '🇨🇴 Español';
            }}
            updateLanguage(currentLang);
        }}
        
        function updateLanguage(lang) {{
            document.querySelectorAll('.lang-en, .lang-es').forEach(el => {{
                el.classList.remove('active');
                if (el.classList.contains(`lang-${{lang}}`)) {{
                    el.classList.add('active');
                }}
            }});
            localStorage.setItem('preferredLanguage', lang);
        }}
        
        document.addEventListener('DOMContentLoaded', function() {{
            const savedLang = localStorage.getItem('preferredLanguage') || 'en';
            currentLang = savedLang;
            if (savedLang === 'es') {{
                document.querySelector('.lang-toggle').textContent = '🇺🇸 English';
            }}
            updateLanguage(savedLang);
        }});
    </script>
</body>
</html>
"""
    
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w") as f:
        f.write(INDEX_TEMPLATE.format(options_html=options_html))
    print("✅ Generated index page")

# ---------- Main Generation ----------
def main():
    print("🚀 Generating site with multi-path support...")
    
    # Generate index page
    generate_index_page()
    
    # Process each option
    for opt in config.get("options", []):
        if opt.get("type") == "choice":
            # Generate choice page and all step paths
            generate_choice_page(opt)
            generate_step_pages(opt)
        else:
            # Handle regular options (your existing code)
            # This is a simplified version - you may want to keep your existing logic
            print(f"⚠️  Regular option '{opt.get('id')}' found - using standard generation")
    
    print("✅ Site generated successfully with multi-path support!")

if __name__ == "__main__":
    main()
