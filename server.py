import http.server
import json
import urllib.request
import urllib.error
import os
import sys

PORT = 3000

def call_gemini(model, payload):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise Exception("GEMINI_API_KEY environment variable is missing. Please configure it in your Settings / Env settings.")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    req_body = json.dumps(payload).encode("utf-8")
    
    req = urllib.request.Request(
        url,
        data=req_body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "aistudio-build"
        },
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = response.read().decode("utf-8")
            return json.loads(res_data)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print("Gemini API HTTP Error:", error_body)
        raise Exception(f"Gemini API returned error {e.code}: {error_body}")
    except Exception as e:
        print("Gemini API Connection Error:", str(e))
        raise Exception(f"Failed to connect to Gemini API: {str(e)}")

class BrandIdentityHandler(http.server.BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        # Serve index.html or other static files
        if self.path == "/" or self.path == "/index.html" or self.path.startswith("/?"):
            self.serve_file("index.html", "text/html")
        elif self.path == "/favicon.ico":
            self.send_response(404)
            self.end_headers()
        else:
            # SPA fallback: if file doesn't exist, serve index.html
            clean_path = self.path.lstrip("/")
            if os.path.exists(clean_path) and os.path.isfile(clean_path):
                ext = os.path.splitext(clean_path)[1].lower()
                mime = "text/plain"
                if ext == ".css": mime = "text/css"
                elif ext == ".js": mime = "application/javascript"
                elif ext == ".png": mime = "image/png"
                elif ext == ".jpg" or ext == ".jpeg": mime = "image/jpeg"
                elif ext == ".svg": mime = "image/svg+xml"
                self.serve_file(clean_path, mime)
            else:
                self.serve_file("index.html", "text/html")

    def do_POST(self):
        if self.path == "/api/brand/generate":
            self.handle_generate()
        elif self.path == "/api/brand/generate-image":
            self.handle_generate_image()
        elif self.path == "/api/brand/chat":
            self.handle_chat()
        elif self.path == "/api/brand/challenge":
            self.handle_challenge()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Endpoint not found: {self.path}"}).encode('utf-8'))

    def serve_file(self, filename, content_type):
        try:
            if not os.path.exists(filename):
                # Try relative path
                base_name = os.path.basename(filename)
                if os.path.exists(base_name):
                    filename = base_name
                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(f"File not found: {filename}".encode('utf-8'))
                    return

            with open(filename, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Internal server error: {str(e)}".encode('utf-8'))

    def handle_generate(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data.decode('utf-8'))
            
            company_name = body.get("companyName")
            industry = body.get("industry", "General / Dynamic")
            mission = body.get("mission")
            target_audience = body.get("targetAudience", "General Public")
            brand_values = body.get("brandValues", [])
            aesthetic_style = body.get("aestheticStyle", "Modern Minimalist")
            
            if not company_name or not mission:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Company name and mission are required"}).encode('utf-8'))
                return

            prompt = f"""Generate a comprehensive and professional "Brand Bible" for the following company:
- Company Name: {company_name}
- Industry: {industry}
- Mission / Description: {mission}
- Target Audience: {target_audience}
- Brand Values: {", ".join(brand_values) if brand_values else "Innovative, Quality, User-centric"}
- Visual Aesthetic / Tone Preference: {aesthetic_style}

Ensure all details are highly tailored, realistic, and inspiring. For the logo concepts, describe both a typographic logo and a graphic submark, and write descriptive image generation prompts for each. Also provide a beautiful placeholder typographic SVG for both concepts. Ensure placeholders are stunning vector layouts, incorporating the company name inside, fully self-contained."""

            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "systemInstruction": {"parts": [{"text": "You are a world-class Elite Brand Identity strategist, typography expert, and Visual Creative Director. You create highly cohesive and inspiring Brand Bibles for companies."}]},
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "responseSchema": {
                        "type": "OBJECT",
                        "properties": {
                            "tagline": {"type": "STRING", "description": "A memorable, catchy, and inspiring brand tagline or slogan."},
                            "positioningStatement": {"type": "STRING", "description": "A solid brand positioning statement explaining the unique value proposition (1-2 paragraphs)."},
                            "brandKeywords": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"},
                                "description": "3 to 5 brand personality keywords or traits (e.g. 'Sophisticated', 'Bold', 'Trustworthy')."
                            },
                            "colors": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "hex": {"type": "STRING", "description": "Hex code starting with #. Example: '#1E293B'"},
                                        "name": {"type": "STRING", "description": "A creative, evocative name for the color. Example: 'Midnight Slate'"},
                                        "role": {"type": "STRING", "description": "The role of this color (e.g., 'Primary', 'Secondary', 'Accent', 'Background', 'Text')"},
                                        "usage": {"type": "STRING", "description": "Detailed guideline on how and when to use this color."}
                                    },
                                    "required": ["hex", "name", "role", "usage"]
                                },
                                "description": "A 5-color cohesive palette designed for digital and print brand applications."
                            },
                            "fonts": {
                                "type": "OBJECT",
                                "properties": {
                                    "headerFont": {"type": "STRING", "description": "A beautiful Google Font name for headers/titles (e.g., 'Outfit', 'Playfair Display', 'Space Grotesk')."},
                                    "headerFontCategory": {"type": "STRING", "description": "Font category (e.g., 'Sans-serif', 'Serif', 'Display', 'Monospace')."},
                                    "headerUsage": {"type": "STRING", "description": "Instructions on font-weight, letter-spacing, and casing for titles."},
                                    "bodyFont": {"type": "STRING", "description": "A highly readable Google Font name for body copy (e.g., 'Inter', 'Lora', 'Plus Jakarta Sans')."},
                                    "bodyFontCategory": {"type": "STRING", "description": "Font category (e.g., 'Sans-serif', 'Serif')."},
                                    "bodyUsage": {"type": "STRING", "description": "Instructions on line-height and weight for body reading."},
                                    "fontRationale": {"type": "STRING", "description": "Visual and psychological rationale of why this font combination perfectly fits the brand's mission."}
                                },
                                "required": ["headerFont", "headerFontCategory", "headerUsage", "bodyFont", "bodyFontCategory", "bodyUsage", "fontRationale"]
                            },
                            "logoConcepts": {
                                "type": "OBJECT",
                                "properties": {
                                    "primaryLogoDescription": {"type": "STRING", "description": "A narrative description of the primary logo layout, visual elements, and emotional tone."},
                                    "primaryLogoPrompt": {"type": "STRING", "description": "A highly descriptive prompt to feed into an AI image generator to create this primary logo. It should specify design style (e.g. vector graphic, minimalist flat logo, dark background, sharp lines, clean emblem) and colors."},
                                    "secondaryLogoDescription": {"type": "STRING", "description": "A narrative description of the secondary mark, icon, or submark."},
                                    "secondaryLogoPrompt": {"type": "STRING", "description": "A highly descriptive prompt to generate the secondary mark or brand icon using an AI image generator. Mention design style (e.g. minimalist symbol, modern brand icon, isolated on dark/light solid background)."},
                                    "placeholderPrimarySvg": {"type": "STRING", "description": "A complete, self-contained SVG string that presents a gorgeous typographic layout of the company name matching the brand style. Ensure it looks styled with custom fonts, colors, and layout (incorporate the company name directly). Ensure it has viewBox, width, height, and does not contain raw HTML wrapper tags. Safe style choices include crisp typography, geometric background panels, or a stylized lettermark."},
                                    "placeholderSecondarySvg": {"type": "STRING", "description": "A complete, self-contained SVG string representing a styled icon or emblem for the submark. It must be a valid, beautiful, and fully self-contained SVG representing the secondary logo concept."}
                                },
                                "required": ["primaryLogoDescription", "primaryLogoPrompt", "secondaryLogoDescription", "secondaryLogoPrompt", "placeholderPrimarySvg", "placeholderSecondarySvg"]
                            },
                            "brandVoice": {
                                "type": "OBJECT",
                                "properties": {
                                    "personality": {"type": "STRING", "description": "A summary of the brand's personality in 2-4 words (e.g. 'friendly and approachable,' 'authoritative and expert,' 'playful and innovative')."},
                                    "personalityDescription": {"type": "STRING", "description": "A description of how this personality translates to the brand's voice and behavior based on the company's mission."},
                                    "toneGuidelines": {
                                        "type": "ARRAY",
                                        "items": {
                                            "type": "OBJECT",
                                            "properties": {
                                                "context": {"type": "STRING", "description": "The communication context (e.g., 'Social Media', 'Customer Support', 'Press Releases')."},
                                                "guideline": {"type": "STRING", "description": "Specific advice on tone, word choice, and demeanor for this context."}
                                            },
                                            "required": ["context", "guideline"]
                                        },
                                        "description": "Suggested tone guidelines for different communication contexts."
                                    }
                                },
                                "required": ["personality", "personalityDescription", "toneGuidelines"]
                            }
                        },
                        "required": ["tagline", "positioningStatement", "brandKeywords", "colors", "fonts", "logoConcepts", "brandVoice"]
                    }
                }
            }
            
            gemini_response = call_gemini("gemini-2.5-flash", payload)
            result_text = gemini_response["candidates"][0]["content"]["parts"][0]["text"]
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(result_text.encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    def handle_generate_image(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data.decode('utf-8'))
            
            prompt = body.get("prompt")
            size = body.get("size", "1K")
            
            if not prompt:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Prompt is required"}).encode('utf-8'))
                return
            
            # Request image generation via gemini-3-pro-image-preview
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "imageConfig": {
                        "aspectRatio": "1:1",
                        "imageSize": size
                    }
                }
            }
            
            base64_image = ""
            try:
                gemini_response = call_gemini("gemini-3-pro-image-preview", payload)
                parts = gemini_response["candidates"][0]["content"]["parts"]
                for part in parts:
                    if "inlineData" in part:
                        base64_image = part["inlineData"]["data"]
                        break
            except Exception as img_err:
                print("Image generation model failed, running SVG fallback. Error:", str(img_err))
                
            if not base64_image:
                # High-fidelity SVG Fallback using gemini-2.5-flash
                fallback_prompt = f"""You are a professional logo designer and SVG layout developer. 
Create an incredibly beautiful, highly polished, fully custom, valid SVG XML layout for the following brand logo concept: "{prompt}".
Your response MUST be the raw SVG XML only. Absolutely NO Markdown wrappers, NO code blocks, NO HTML outer tags. Only start with <svg ...> and end with </svg>.
Ensure it incorporates gorgeous modern colors, smooth paths, clean font layouts, and has perfect viewBox scaling. It should look ultra-premium."""
                
                fallback_payload = {
                    "contents": [{"parts": [{"text": fallback_prompt}]}],
                    "systemInstruction": {"parts": [{"text": "You are a master of inline SVG vector graphic generation. Return pure SVG string with no explanations or code formatting fences."}]}
                }
                
                try:
                    fallback_res = call_gemini("gemini-2.5-flash", fallback_payload)
                    svg_text = fallback_res["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if "```xml" in svg_text:
                        svg_text = svg_text.split("```xml")[1].split("```")[0].strip()
                    elif "```html" in svg_text:
                        svg_text = svg_text.split("```html")[1].split("```")[0].strip()
                    elif "```" in svg_text:
                        svg_text = svg_text.split("```")[1].split("```")[0].strip()
                    
                    import urllib.parse
                    safe_svg = urllib.parse.quote(svg_text)
                    image_url = f"data:image/svg+xml;utf8,{safe_svg}"
                    
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"imageUrl": image_url}).encode('utf-8'))
                    return
                except Exception as fallback_err:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": f"Image and SVG fallback both failed: {str(fallback_err)}"}).encode('utf-8'))
                    return
                
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"imageUrl": f"data:image/png;base64,{base64_image}"}).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    def handle_chat(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data.decode('utf-8'))
            
            messages = body.get("messages", [])
            system_instruction = body.get("systemInstruction", "You are an Elite Brand Identity Consultant advising the user.")
            
            contents = []
            for m in messages:
                role = "model" if m.get("role") == "assistant" else "user"
                contents.append({
                    "role": role,
                    "parts": [{"text": m.get("content", "")}]
                })
                
            payload = {
                "contents": contents,
                "systemInstruction": {"parts": [{"text": system_instruction}]}
            }
            
            gemini_response = call_gemini("gemini-2.5-flash", payload)
            reply = gemini_response["candidates"][0]["content"]["parts"][0]["text"]
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"reply": reply}).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    def handle_challenge(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data.decode('utf-8'))
            
            company_name = body.get("companyName")
            industry = body.get("industry", "General / Dynamic")
            mission = body.get("mission")
            target_audience = body.get("targetAudience", "General Public")
            positioning_statement = body.get("positioningStatement", "Not provided yet")
            brand_values = body.get("brandValues", [])
            
            if not company_name or not mission:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Company name and mission are required for challenge audit."}).encode('utf-8'))
                return
                
            prompt = f"""Critically stress-test, dissect, and critique the following brand strategy as an uncompromising, sharp, and highly analytical Devil's Advocate:
- Company Name: {company_name}
- Industry: {industry}
- Mission / Description: {mission}
- Target Audience: {target_audience}
- Positioning Statement: {positioning_statement}
- Brand Values: {", ".join(brand_values) if brand_values else "Not specified"}

Your goal is to expose weak business assumptions, identify generic styling or messaging clichés, warn about saturated market hazards, and describe how a cynical customer would doubt their claims. Be sharp, polite but uncompromisingly honest, and extremely insightful. 
Then, provide 3 tough questions that they absolutely must resolve.
Finally, provide highly constructive, creative suggestions on how they can refine their language or positioning to become bulletproof."""

            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "systemInstruction": {"parts": [{"text": "You are an Elite Venture Strategist, visual design critic, and professional Devil's Advocate. You stress-test brand assumptions and help startups identify positioning blindspots, providing deep strategic insights and constructive refinements."}]},
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "responseSchema": {
                        "type": "OBJECT",
                        "properties": {
                            "criticalCritique": {
                                "type": "STRING",
                                "description": "A comprehensive critical analysis of the brand strategy's weak spots, oversaturations, and cliché risks (1-2 paragraphs)."
                            },
                            "pitfalls": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "title": {"type": "STRING", "description": "Title of the risk (e.g. 'Eco-Cliché Saturation')."},
                                        "description": {"type": "STRING", "description": "Detailed explanation of why this represents a major risk."}
                                    },
                                    "required": ["title", "description"]
                                },
                                "description": "Exactly 2 to 3 major strategic or visual pitfalls they face."
                            },
                            "hardQuestions": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"},
                                "description": "Exactly 3 highly direct, strategic, and challenging questions."
                            },
                            "refinementPivots": {
                                "type": "STRING",
                                "description": "Actionable, constructive guidelines on how they should refine their positioning statement, wording, or target messaging to resolve these criticisms."
                            }
                        },
                        "required": ["criticalCritique", "pitfalls", "hardQuestions", "refinementPivots"]
                    }
                }
            }
            
            gemini_response = call_gemini("gemini-2.5-flash", payload)
            result_text = gemini_response["candidates"][0]["content"]["parts"][0]["text"]
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(result_text.encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

def run(server_class=http.server.HTTPServer, handler_class=BrandIdentityHandler):
    server_address = ('0.0.0.0', PORT)
    httpd = server_class(server_address, handler_class)
    print(f"Python server starting on port {PORT}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == '__main__':
    run()
