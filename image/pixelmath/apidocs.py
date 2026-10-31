"""OpenAPI 3 description and Postman collection for the HTTP API.

    python3 -m pixelmath.apidocs api/        # rewrites api/openapi.json and api/postman_collection.json
"""
import json
import os
import sys

from . import __version__

ERR = {"description": "Error", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}}


def _err(desc):
    return {"description": desc, "content": ERR["content"]}


def openapi(cfg=None):
    from .server import Config
    cfg = cfg or Config()
    url = "http://127.0.0.1:8000" if not cfg.port else "http://%s:%d" % (
        "[%s]" % cfg.host if ":" in cfg.host else cfg.host, cfg.port)
    image = {"image/png": {"schema": {"type": "string", "format": "binary"}},
             "image/bmp": {"schema": {"type": "string", "format": "binary"}}}
    secured = [{"ApiKeyAuth": []}, {"BearerAuth": []}]
    return {
        "openapi": "3.0.3",
        "info": {"title": "PixelMath API", "version": __version__,
                 "description": "Text-to-image engine written from scratch (no external model). "
                                "Generate images, inspect how prompts are parsed, and train the engine on your own images."},
        "servers": [{"url": url}],
        "security": secured,
        "paths": {
            "/health": {"get": {"summary": "Liveness check", "operationId": "health", "security": [],
                                "responses": {"200": {"description": "Server is up", "content": {"application/json": {
                                    "schema": {"$ref": "#/components/schemas/Health"}}}}}}},
            "/generate": {
                "post": {"summary": "Generate an image from a prompt", "operationId": "generate",
                         "requestBody": {"required": True, "content": {"application/json": {
                             "schema": {"$ref": "#/components/schemas/GenerateRequest"}}}},
                         "responses": {
                             "200": {"description": "PNG/BMP bytes (response=binary) or JSON with base64 (response=base64). "
                                                    "Headers: X-PixelMath-Mode, X-PixelMath-Seed, X-Render-Seconds",
                                     "content": {**image, "application/json": {
                                         "schema": {"$ref": "#/components/schemas/GenerateJson"}}}},
                             "400": _err("Invalid parameter"), "401": _err("Missing or invalid API key"),
                             "415": _err("Content-Type must be application/json"),
                             "503": _err("Server busy: retry after the Retry-After seconds")}},
                "get": {"summary": "Generate an image (query parameters, handy in a browser)", "operationId": "generateGet",
                        "parameters": [
                            {"name": "prompt", "in": "query", "required": True, "schema": {"type": "string", "maxLength": 2000}},
                            {"name": "size", "in": "query", "schema": {"type": "integer", "default": 512, "minimum": 16, "maximum": 2048}},
                            {"name": "width", "in": "query", "schema": {"type": "integer"}},
                            {"name": "height", "in": "query", "schema": {"type": "integer"}},
                            {"name": "seed", "in": "query", "schema": {"type": "integer", "default": 0}},
                            {"name": "format", "in": "query", "schema": {"type": "string", "enum": ["png", "bmp"], "default": "png"}},
                            {"name": "learned", "in": "query", "schema": {"type": "string", "enum": ["auto", "always", "blend", "off"], "default": "auto"}},
                            {"name": "response", "in": "query", "schema": {"type": "string", "enum": ["binary", "base64"], "default": "binary"}}],
                        "responses": {"200": {"description": "Image bytes", "content": image},
                                      "400": _err("Invalid parameter"), "401": _err("Missing or invalid API key"),
                                      "503": _err("Server busy")}}},
            "/create": {"post": {
                "summary": "Creative mode: propose variations, let a critic judge them, breed the best",
                "description": "temperature 0 = the plain render (no search). Above 0 the engine adds related props, time/weather/"
                               "background/palette ideas and new layouts, throws away any variation that drops or alters what the "
                               "prompt asked for, and keeps improving the survivors with a small genetic search. The response says "
                               "what it thought (header X-PixelMath-Prompt = the prompt it finally rendered; the same prompt + seed "
                               "reproduces the image through /generate). With response=base64 the JSON also holds `creation` "
                               "(thinking notes, scores, generations, rejected-by-critic counts, alternatives).",
                "operationId": "create",
                "requestBody": {"required": True, "content": {"application/json": {
                    "schema": {"$ref": "#/components/schemas/CreateRequest"}}}},
                "responses": {"200": {"description": "PNG/BMP bytes or JSON with base64 + creation report",
                                      "content": {**image, "application/json": {"schema": {"$ref": "#/components/schemas/GenerateJson"}}}},
                              "400": _err("Invalid parameter"), "401": _err("Missing or invalid API key"),
                              "503": _err("Server busy")}}},
            "/imagine": {"post": {
                "summary": "Mash two random ideas together; the critic rejects the ones that do not work",
                "description": "Like /create, but the idea itself is random (e.g. 'excavator and sofa'). Optional `anchor` keeps "
                               "one idea of yours (e.g. 'cat') and mashes it with something random.",
                "operationId": "imagine",
                "requestBody": {"required": True, "content": {"application/json": {
                    "schema": {"$ref": "#/components/schemas/ImagineRequest"}}}},
                "responses": {"200": {"description": "PNG/BMP bytes or JSON with base64 + creation report",
                                      "content": {**image, "application/json": {"schema": {"$ref": "#/components/schemas/GenerateJson"}}}},
                              "400": _err("Invalid parameter"), "401": _err("Missing or invalid API key"),
                              "503": _err("Server busy")}}},
            "/gallery": {
                "get": {"summary": "List saved pictures (newest first)", "operationId": "gallery",
                        "description": "Needs a database (python3 app.py has one; serve.py needs --db). Pictures are saved when a "
                                       "request to /generate, /create or /imagine contains \"save\": true.",
                        "parameters": [{"name": "limit", "in": "query", "schema": {"type": "integer", "default": 48, "maximum": 200}},
                                       {"name": "offset", "in": "query", "schema": {"type": "integer", "default": 0}},
                                       {"name": "favourites", "in": "query", "schema": {"type": "boolean", "default": False}},
                                       {"name": "q", "in": "query", "schema": {"type": "string", "maxLength": 100}}],
                        "responses": {"200": {"description": "{items:[...], total}"}, "404": _err("No database")}},
                "delete": {"summary": "Delete saved pictures", "operationId": "galleryClear",
                           "parameters": [{"name": "keep_favourites", "in": "query", "schema": {"type": "boolean", "default": True}}],
                           "responses": {"200": {"description": "{deleted: n}"}}}},
            "/gallery/{id}": {
                "get": {"summary": "One saved picture: prompt, seed, parameters and the creative report", "operationId": "galleryItem",
                        "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                        "responses": {"200": {"description": "Details"}, "404": _err("Unknown id")}},
                "delete": {"summary": "Delete one saved picture", "operationId": "galleryDelete",
                           "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                           "responses": {"200": {"description": "{deleted: 1}"}, "404": _err("Unknown id")}}},
            "/gallery/{id}/image": {"get": {"summary": "The saved picture (PNG/BMP bytes)", "operationId": "galleryImage",
                                            "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                                            "responses": {"200": {"description": "Image", "content": image}}}},
            "/gallery/{id}/thumb": {"get": {"summary": "A small PNG preview (max 160 px)", "operationId": "galleryThumb",
                                            "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                                            "responses": {"200": {"description": "PNG", "content": image}}}},
            "/gallery/{id}/favourite": {"post": {"summary": "Mark or unmark a favourite (favourites are never dropped)", "operationId": "galleryFavourite",
                                                 "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                                                 "requestBody": {"required": True, "content": {"application/json": {"schema": {
                                                     "type": "object", "required": ["favourite"], "properties": {"favourite": {"type": "boolean"}}}}}},
                                                 "responses": {"200": {"description": "{id, favourite}"}}}},
            "/dataset": {"get": {"summary": "The images the model was trained on (dataset manager)", "operationId": "dataset",
                                 "description": "Works without a database too (then only the coarse colour preview exists).",
                                 "parameters": [{"name": "limit", "in": "query", "schema": {"type": "integer", "default": 60, "maximum": 200}},
                                                {"name": "offset", "in": "query", "schema": {"type": "integer", "default": 0}},
                                                {"name": "q", "in": "query", "schema": {"type": "string"}}],
                                 "responses": {"200": {"description": "{total, items:[{id, caption, file, added, job_id, original_preview}], grid}"}}}},
            "/dataset/delete": {"post": {"summary": "Remove trained images and retrain on the rest (asynchronous)", "operationId": "datasetDelete",
                                         "requestBody": {"required": True, "content": {"application/json": {"schema": {
                                             "type": "object", "required": ["ids"], "properties": {"ids": {"type": "array", "items": {"type": "string"}}}}}}},
                                         "responses": {"202": {"description": "{job_id, removed, remaining}: poll /jobs/{id}"},
                                                       "404": _err("None of the ids are in the model"), "409": _err("Training busy")}}},
            "/dataset/{id}": {"delete": {"summary": "Remove one trained image and retrain", "operationId": "datasetDeleteOne",
                                         "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                                         "responses": {"202": {"description": "Job accepted"}, "404": _err("Unknown id"), "409": _err("Training busy")}}},
            "/dataset/{id}/image": {"get": {"summary": "Preview of a trained image (PNG)", "operationId": "datasetImage",
                                            "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                                            "responses": {"200": {"description": "PNG", "content": image}}}},
            "/dataset/{id}/caption": {"post": {"summary": "Change a trained image's caption and retrain", "operationId": "datasetCaption",
                                               "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                                               "requestBody": {"required": True, "content": {"application/json": {"schema": {
                                                   "type": "object", "required": ["caption"], "properties": {"caption": {"type": "string", "maxLength": 200}}}}}},
                                               "responses": {"202": {"description": "Job accepted"}, "400": _err("Bad caption"), "404": _err("Unknown id")}}},
            "/scene": {"post": {
                "summary": "One premium niche picture for a website (restaurant, gym, dental, saas ...) with a built-in judge",
                "description": "The niche, mood and accent are read from the prompt (\"gym with dumbbells in red light\"). If no niche fits, a neutral abstract "
                               "in the accent colour is returned and the report says fallback: true (never a wrong subject). With text_zone the "
                               "area stays calm so text on it has contrast >= 4.5:1 (report.text_color says which colour to use). "
                               "Binary answers carry X-PixelMath-Niche / -Fallback / -Redrawn / -Text-Color headers; response=base64 returns the full report.",
                "operationId": "scene",
                "requestBody": {"required": True, "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SceneRequest"}}}},
                "responses": {"200": {"description": "JPEG/PNG bytes or JSON with base64 + report", "content": {**image, "application/json": {}}},
                              "400": _err("Invalid parameter"), "401": _err("Missing or invalid API key"), "503": _err("Server busy")}}},
            "/set": {"post": {
                "summary": "3 to 8 pictures for one site in one style: hero (text zone), about, gallery tiles",
                "description": "Same niche, palette, mood and light; different camera and composition. The judge redraws any picture too close to another "
                               "(perceptual hash distance) and reports redrawn / min_distance / palette_family / hero text contrast. response=zip "
                               "(default) returns hero.jpg, about.jpg, tile-N.jpg and report.json; response=base64 returns JSON. Takes about 5-12 s.",
                "operationId": "set",
                "requestBody": {"required": True, "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SetRequest"}}}},
                "responses": {"200": {"description": "zip or JSON", "content": {"application/zip": {"schema": {"type": "string", "format": "binary"}},
                                                                                "application/json": {}}},
                              "400": _err("Invalid parameter"), "401": _err("Missing or invalid API key"), "503": _err("Server busy")}}},
            "/spec": {"post": {
                "summary": "One picture for the owner's picture spec: \"<subject>, for a <business> website. ... Palette: accent #x on #y.\"",
                "description": "The business named in the prompt decides the scene (99 businesses + 20 business types of the spec), the slot (hero-1..3, about, gallery-1..6, "
                               "card-1..6, team-1..3, background) decides size (1600x900, 1200x900, 900x900, 800x600, 600x600, 1600x900), camera and text zone. "
                               "No text, letters or numbers are ever drawn; an unknown business gets a neutral abstract (fallback: true). Palette: accent and background "
                               "from the prompt or the accent / bg fields; a dark background gives a dark picture. The spec ships with the package "
                               "(PIXELMATH_SPEC_DIR replaces it); 501 spec_unavailable only when its data files are missing from the installation.",
                "operationId": "spec",
                "requestBody": {"required": True, "content": {"application/json": {"schema": {
                    "type": "object", "required": ["prompt"], "additionalProperties": False,
                    "properties": {"prompt": {"type": "string"}, "slot": {"type": "string", "description": "hero-1, about, gallery-3, card-2, team-1, background ..."},
                                   "seed": {"type": "integer"}, "accent": {"type": "string"}, "bg": {"type": "string"}, "niche": {"type": "string"},
                                   "design_style": {"type": "string"}, "format": {"type": "string", "enum": ["jpeg", "png"]},
                                   "response": {"type": "string", "enum": ["image", "base64"]}}}}}},
                "responses": {"200": {"description": "JPEG/PNG bytes or JSON with base64 + report", "content": {**image, "application/json": {}}},
                              "400": _err("Invalid parameter"), "401": _err("Missing or invalid API key"),
                              "403": _err("Browser request from another site (cross_origin)"),
                              "501": _err("The spec's data files are missing from this installation (spec_unavailable)"), "503": _err("Server busy")}}},
            "/spec/business": {"post": {
                "summary": "All 20 pictures of one spec business (3 hero, about, 6 gallery, 6 card, 3 team, background) as a zip with manifest.json",
                "description": "Uses the spec's own 20 prompts of the business, one palette (palette: 0 or 1) and one style; pictures of the scene slots differ by at "
                               "least 8 of 63 perceptual-hash bits. Takes about a minute.",
                "operationId": "specBusiness",
                "requestBody": {"required": True, "content": {"application/json": {"schema": {
                    "type": "object", "required": ["business"], "additionalProperties": False,
                    "properties": {"business": {"type": "string", "description": "id from GET /spec/businesses"}, "palette": {"type": "integer"},
                                   "seed": {"type": "integer"}, "format": {"type": "string", "enum": ["jpeg", "png"]}}}}}},
                "responses": {"200": {"description": "zip", "content": {"application/zip": {"schema": {"type": "string", "format": "binary"}}}},
                              "400": _err("Invalid parameter"), "401": _err("Missing or invalid API key"),
                              "403": _err("Browser request from another site (cross_origin)"),
                              "501": _err("The spec's data files or prompt list are missing from this installation (spec_unavailable, spec_prompts_missing)"),
                              "503": _err("Server busy")}}},
            "/spec/businesses": {"get": {"summary": "The spec's 99 businesses with their niche and palettes", "operationId": "specBusinesses",
                                         "responses": {"200": {"description": "{businesses: [{id, name, niche, palettes}]}"}, "401": _err("Missing or invalid API key"),
                                                       "501": _err("The spec's data files are missing from this installation (spec_unavailable)")}}},
            "/niches": {"get": {"summary": "The niches the studio can draw", "operationId": "niches",
                                "responses": {"200": {"description": "{niches: [{id, title, group, accent, mood}]}"}, "401": _err("Missing or invalid API key")}}},
            "/parse": {"post": {"summary": "Show how a prompt is understood", "operationId": "parse",
                                "requestBody": {"required": True, "content": {"application/json": {"schema": {
                                    "type": "object", "required": ["prompt"], "additionalProperties": False,
                                    "properties": {"prompt": {"type": "string"}}}}}},
                                "responses": {"200": {"description": "Parse result", "content": {"application/json": {
                                    "schema": {"$ref": "#/components/schemas/ParseResult"}}}},
                                    "400": _err("Invalid parameter"), "401": _err("Missing or invalid API key")}}},
            "/model": {"get": {"summary": "Info about the loaded trained model", "operationId": "model",
                               "responses": {"200": {"description": "Model info", "content": {"application/json": {
                                   "schema": {"$ref": "#/components/schemas/ModelInfo"}}}},
                                   "401": _err("Missing or invalid API key")}}},
            "/train": {"post": {
                "summary": "Train on an uploaded zip of images + captions (asynchronous)",
                "description": "Zip layout: images (png/jpg/bmp) plus optional captions.csv (file,caption), captions.json "
                               "or a .txt next to each image. Needs the server started with --model PATH. Returns a job to poll.",
                "operationId": "train",
                "requestBody": {"required": True, "content": {
                    "multipart/form-data": {"schema": {"type": "object", "required": ["data"], "properties": {
                        "data": {"type": "string", "format": "binary", "description": "the zip file"},
                        "epochs": {"type": "integer", "default": 80, "minimum": 1, "maximum": 500},
                        "lr": {"type": "number", "default": 0.3}, "l2": {"type": "number", "default": 0.0001},
                        "val_frac": {"type": "number", "default": 0.15}, "seed": {"type": "integer", "default": 0},
                        "fresh": {"type": "boolean", "default": False, "description": "ignore the existing model"},
                        "grid": {"type": "integer", "default": 16, "description": "new models only"},
                        "refit": {"type": "boolean", "default": True}}}},
                    "application/zip": {"schema": {"type": "string", "format": "binary"}}}},
                "responses": {"202": {"description": "Accepted", "content": {"application/json": {
                    "schema": {"$ref": "#/components/schemas/TrainAccepted"}}}},
                    "400": _err("Bad zip or parameter"), "401": _err("Missing or invalid API key"),
                    "403": _err("Training disabled (no --model)"), "409": _err("A training job is already running"),
                    "413": _err("Upload or unzipped data too large"), "415": _err("Unsupported Content-Type")}}},
            "/jobs/{id}": {"get": {"summary": "Training job status", "operationId": "job",
                                   "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                                   "responses": {"200": {"description": "Job", "content": {"application/json": {
                                       "schema": {"$ref": "#/components/schemas/Job"}}}},
                                       "404": _err("Unknown job"), "401": _err("Missing or invalid API key")}}},
            "/jobs": {"get": {"summary": "Recent training jobs", "operationId": "jobs",
                              "responses": {"200": {"description": "Job list"}, "401": _err("Missing or invalid API key")}}},
        },
        "components": {
            "securitySchemes": {"ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-API-Key"},
                                "BearerAuth": {"type": "http", "scheme": "bearer"}},
            "schemas": {
                "Error": {"type": "object", "properties": {"error": {"type": "object", "properties": {
                    "code": {"type": "string"}, "message": {"type": "string"}}}}},
                "Health": {"type": "object", "properties": {
                    "status": {"type": "string"}, "version": {"type": "string"}, "model_loaded": {"type": "boolean"},
                    "training_enabled": {"type": "boolean"}, "auth_required": {"type": "boolean"}}},
                "GenerateRequest": {"type": "object", "required": ["prompt"], "additionalProperties": False, "properties": {
                    "prompt": {"type": "string", "maxLength": 2000, "example": "red house with a tree under a sunset sky"},
                    "size": {"type": "integer", "default": 512, "minimum": 16, "maximum": 2048,
                             "description": "square size; the server may cap it lower (default 1024)"},
                    "width": {"type": "integer"}, "height": {"type": "integer"},
                    "seed": {"type": "integer", "default": 0, "description": "same prompt + seed = same image"},
                    "format": {"type": "string", "enum": ["png", "bmp"], "default": "png"},
                    "learned": {"type": "string", "enum": ["auto", "always", "blend", "off"], "default": "auto"},
                    "response": {"type": "string", "enum": ["binary", "base64"], "default": "binary"},
                    "save": {"type": "boolean", "default": False, "description": "keep the picture in the gallery (needs a database); "
                                                                               "the answer then has gallery_id / header X-PixelMath-Gallery-Id"}}},
                "GenerateJson": {"type": "object", "properties": {
                    "image_base64": {"type": "string"}, "mime": {"type": "string"}, "width": {"type": "integer"},
                    "height": {"type": "integer"}, "seed": {"type": "integer"}, "mode": {"type": "string"},
                    "render_seconds": {"type": "number"}, "gallery_id": {"type": "integer"}, "known_words": {"type": "array", "items": {"type": "string"}}}},
                "CreateRequest": {"type": "object", "required": ["prompt"], "additionalProperties": False, "properties": {
                    "prompt": {"type": "string", "maxLength": 2000, "example": "laptop and coffee cup"},
                    "temperature": {"type": "number", "default": 0.7, "minimum": 0, "maximum": 1,
                                    "description": "0 = safest/plain, 1 = boldest"},
                    "population": {"type": "integer", "default": 8, "minimum": 2, "maximum": 16},
                    "generations": {"type": "integer", "default": 3, "minimum": 0, "maximum": 6},
                    "alternatives": {"type": "integer", "default": 3, "minimum": 0, "maximum": 5},
                    "explore": {"type": "integer", "default": 0, "minimum": 0, "maximum": 500,
                                "description": "judge this many extra random ideas at thumbnail size first, breed from the best"},
                    "max_seconds": {"type": "number", "default": 20, "description": "time budget for the search"},
                    "size": {"type": "integer", "default": 512}, "width": {"type": "integer"}, "height": {"type": "integer"},
                    "seed": {"type": "integer", "default": 0}, "format": {"type": "string", "enum": ["png", "bmp"]},
                    "learned": {"type": "string", "enum": ["auto", "always", "blend", "off"]},
                    "response": {"type": "string", "enum": ["binary", "base64"], "default": "binary"},
                    "save": {"type": "boolean", "default": False}}},
                "ImagineRequest": {"type": "object", "additionalProperties": False, "properties": {
                    "anchor": {"type": "string", "maxLength": 200, "example": "cat", "description": "optional idea to keep"},
                    "temperature": {"type": "number", "default": 0.8, "minimum": 0, "maximum": 1,
                                    "description": "higher = more unrelated pairs"},
                    "attempts": {"type": "integer", "default": 12, "minimum": 1, "maximum": 30},
                    "population": {"type": "integer", "default": 6}, "generations": {"type": "integer", "default": 2},
                    "max_seconds": {"type": "number", "default": 20},
                    "size": {"type": "integer", "default": 512}, "width": {"type": "integer"}, "height": {"type": "integer"},
                    "seed": {"type": "integer", "default": 0}, "format": {"type": "string", "enum": ["png", "bmp"]},
                    "learned": {"type": "string", "enum": ["auto", "always", "blend", "off"]},
                    "response": {"type": "string", "enum": ["binary", "base64"], "default": "binary"},
                    "save": {"type": "boolean", "default": False}}},
                "SceneRequest": {"type": "object", "required": ["prompt"], "additionalProperties": False, "properties": {
                    "prompt": {"type": "string", "example": "wood fired pizza on a board"},
                    "width": {"type": "integer", "default": 640}, "height": {"type": "integer", "default": 400}, "size": {"type": "integer"},
                    "seed": {"type": "integer", "default": 0},
                    "accent": {"type": "string", "example": "#c0392b", "description": "colour name or #rrggbb; the picture follows it"},
                    "mood": {"type": "string", "enum": ["warm", "cool", "dark", "light"]},
                    "text_zone": {"type": "string", "enum": ["left", "center", "bottom", "none"], "default": "none"},
                    "variant": {"type": "string", "enum": ["fit", "close", "detail", "wide", "fit-flip", "close-flip", "detail-flip", "wide-flip"], "default": "fit"},
                    "niche": {"type": "string", "description": "force a niche id (see /niches)"},
                    "format": {"type": "string", "enum": ["jpeg", "png"], "default": "jpeg"}, "quality": {"type": "integer", "default": 72},
                    "use_model": {"type": "boolean", "default": True, "description": "use the trained model's niche classifier and learned accents"},
                    "response": {"type": "string", "enum": ["binary", "base64"], "default": "binary"}}},
                "SetRequest": {"type": "object", "required": ["prompt"], "additionalProperties": False, "properties": {
                    "prompt": {"type": "string", "example": "dental clinic reception, calm blue"}, "count": {"type": "integer", "default": 6, "minimum": 3, "maximum": 8},
                    "seed": {"type": "integer", "default": 0}, "accent": {"type": "string"}, "mood": {"type": "string", "enum": ["warm", "cool", "dark", "light"]},
                    "text_zone": {"type": "string", "enum": ["left", "center", "bottom", "none"], "default": "left", "description": "text zone of the hero picture"},
                    "niche": {"type": "string"}, "format": {"type": "string", "enum": ["jpeg", "png"], "default": "jpeg"}, "quality": {"type": "integer", "default": 72},
                    "use_model": {"type": "boolean", "default": True}, "response": {"type": "string", "enum": ["zip", "base64"], "default": "zip"}}},
                "ParseResult": {"type": "object", "properties": {
                    "mode": {"type": "string"}, "time": {"type": "string", "nullable": True},
                    "flags": {"type": "array", "items": {"type": "string"}},
                    "entities": {"type": "array", "items": {"type": "object"}},
                    "not_in_lexicon": {"type": "array", "items": {"type": "string"}},
                    "model_knows": {"type": "array", "items": {"type": "string"}}}},
                "ModelInfo": {"type": "object", "properties": {
                    "loaded": {"type": "boolean"}, "grid": {"type": "integer"}, "samples": {"type": "integer"},
                    "vocabulary": {"type": "integer"}, "top_words": {"type": "array", "items": {"type": "object"}}}},
                "TrainAccepted": {"type": "object", "properties": {
                    "job_id": {"type": "string"}, "status": {"type": "string"}, "status_url": {"type": "string"}}},
                "Job": {"type": "object", "properties": {
                    "id": {"type": "string"},
                    "status": {"type": "string", "enum": ["queued", "extracting", "reading", "training", "done", "error"]},
                    "message": {"type": "string"}, "epoch": {"type": "integer"}, "epochs": {"type": "integer"},
                    "train_rmse": {"type": "number", "nullable": True}, "val_rmse": {"type": "number", "nullable": True},
                    "images_read": {"type": "integer"}, "skipped_count": {"type": "integer"},
                    "skipped": {"type": "array", "items": {"type": "object"}},
                    "metrics": {"type": "object", "nullable": True}, "error": {"type": "object", "nullable": True}}}}}}


def _url(path, query=None):
    raw = "{{baseUrl}}/" + path
    u = {"raw": raw, "host": ["{{baseUrl}}"], "path": [p for p in path.split("/") if p]}
    if query:
        u["query"] = [{"key": k, "value": v} for k, v in query]
        u["raw"] = raw + "?" + "&".join("%s=%s" % (k, v) for k, v in query)
    return u


def _json_body(obj):
    return {"mode": "raw", "raw": json.dumps(obj, indent=2), "options": {"raw": {"language": "json"}}}


def postman_collection():
    def req(name, method, path, body=None, query=None, desc="", events=None):
        r = {"method": method, "header": [], "url": _url(path, query), "description": desc}
        if body is not None:
            r["body"] = body
            if body["mode"] == "raw":
                r["header"].append({"key": "Content-Type", "value": "application/json"})
        item = {"name": name, "request": r}
        if events:
            item["event"] = events
        return item

    save_job = [{"listen": "test", "script": {"type": "text/javascript", "exec": [
        "const j = pm.response.json();",
        "if (j.job_id) { pm.collectionVariables.set('jobId', j.job_id); }"]}}]
    form = lambda: {"mode": "formdata", "formdata": [  # noqa: E731
        {"key": "data", "type": "file", "src": [], "description": "zip of images + captions.csv"},
        {"key": "epochs", "value": "80", "type": "text"},
        {"key": "fresh", "value": "false", "type": "text"}]}
    zip_item = req("Train: raw zip body", "POST", "train", {"mode": "file", "file": {}}, query=[("epochs", "80")],
                   events=save_job, desc="Alternative: body = binary zip, Content-Type application/zip.")
    zip_item["request"]["header"].append({"key": "Content-Type", "value": "application/zip"})
    return {
        "info": {"name": "PixelMath API", "description": "Requests for the PixelMath HTTP API. Set baseUrl (and apiKey if "
                                                          "the server was started with one).",
                 "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"},
        "auth": {"type": "apikey", "apikey": [{"key": "key", "value": "X-API-Key", "type": "string"},
                                              {"key": "value", "value": "{{apiKey}}", "type": "string"},
                                              {"key": "in", "value": "header", "type": "string"}]},
        "variable": [{"key": "baseUrl", "value": "http://127.0.0.1:8000"}, {"key": "apiKey", "value": ""},
                     {"key": "jobId", "value": ""}],
        "item": [
            req("Health", "GET", "health", desc="Is the server up? No API key needed."),
            req("Generate image (JSON -> PNG)", "POST", "generate", _json_body(
                {"prompt": "red house with a tree under a sunset sky", "size": 512, "seed": 0, "format": "png"}),
                desc="Returns the PNG. Use Send and Download, or the Preview tab."),
            req("Generate image (GET query)", "GET", "generate",
                query=[("prompt", "cyberpunk neo city at night"), ("size", "512")],
                desc="Same as POST but with query parameters; also works in a browser."),
            req("Generate as base64 JSON", "POST", "generate", _json_body(
                {"prompt": "blue ocean with a boat and the sun", "size": 256, "response": "base64"}),
                desc="Returns {image_base64, mime, mode, ...} for apps that want JSON."),
            req("Generate with trained model", "POST", "generate", _json_body(
                {"prompt": "aqua mossy", "size": 256, "learned": "always"}),
                desc="Uses the trained model for words the built-in lexicon does not know."),
            req("Create (creative mode)", "POST", "create", _json_body(
                {"prompt": "laptop and coffee cup", "temperature": 0.8, "population": 8, "generations": 3, "size": 512,
                 "response": "base64"}),
                desc="Variations + critic + genetic search. With response=base64 the JSON has `creation.thinking` and scores. "
                     "Use response=binary for the PNG itself (headers X-PixelMath-Prompt / -Seed / -Score)."),
            req("Imagine (random mash-up)", "POST", "imagine", _json_body(
                {"anchor": "cat", "temperature": 0.9, "attempts": 12, "size": 512, "response": "base64"}),
                desc="Two ideas mashed together; the critic rejects mash-ups that do not work. Leave anchor out for fully random."),
            req("Generate and save to gallery", "POST", "generate", _json_body(
                {"prompt": "laptop and coffee cup", "size": 384, "save": True, "response": "base64"}),
                desc="Needs a database (python3 app.py has one). The answer contains gallery_id."),
            req("Gallery: list", "GET", "gallery", query=[("limit", "24"), ("favourites", "false")]),
            req("Gallery: one picture (details)", "GET", "gallery/1"),
            req("Gallery: image", "GET", "gallery/1/image"),
            req("Gallery: favourite", "POST", "gallery/1/favourite", _json_body({"favourite": True})),
            req("Studio: one picture (JPEG)", "POST", "scene", _json_body(
                {"prompt": "gym with dumbbells in red light", "width": 1280, "height": 640, "text_zone": "left"}),
                desc="Premium niche picture. Headers X-PixelMath-Niche / -Fallback / -Text-Color tell what was drawn and which text colour to use."),
            req("Studio: one picture with report (base64)", "POST", "scene", _json_body(
                {"prompt": "dental clinic reception, calm blue", "mood": "cool", "text_zone": "left", "response": "base64"}),
                desc="JSON with the image and the judge's report (niche, fallback, scores, redrawn, contrast)."),
            req("Studio: site set (zip)", "POST", "set", _json_body(
                {"prompt": "wood fired pizza on a board", "count": 6, "accent": "#c0392b", "mood": "warm", "text_zone": "left"}),
                desc="hero.jpg, about.jpg, tile-N.jpg and report.json in one zip (Send and Download)."),
            req("Studio: niches", "GET", "niches"),
            req("Spec: businesses", "GET", "spec/businesses", desc="The picture spec's 99 businesses: id, name, niche and palettes."),
            req("Spec: one picture (JPEG)", "POST", "spec", _json_body(
                {"prompt": "Termite drilling (pest control), for a pest control website. Palette: accent #1565c0 on #f5f6f7.", "slot": "gallery-2"}),
                desc="One picture of the spec at its slot's size (hero-1..3 1600x900, about 1200x900, gallery-1..6 900x900, card-1..6 800x600, "
                     "team-1..3 600x600, background 1600x900)."),
            req("Spec: all pictures of a business (zip)", "POST", "spec/business", _json_body({"business": "dental_clinic", "palette": 0}),
                desc="The spec's 20 pictures of one business + manifest.json (Send and Download). Takes about a minute."),
            req("Parse prompt", "POST", "parse", _json_body({"prompt": "ek laal ghar aur do ped, raat"}),
                desc="Shows entities, colours, time of day and which words were not understood."),
            req("Model info", "GET", "model"),
            req("Train: upload zip (form-data)", "POST", "train", form(), events=save_job,
                desc="Pick a zip in the 'data' field. Zip = images + captions.csv (file,caption). Needs --model on the server."),
            zip_item,
            req("Training job status", "GET", "jobs/{{jobId}}", desc="Poll until status is done or error."),
            req("Recent jobs", "GET", "jobs"),
            req("Dataset: list trained images", "GET", "dataset", query=[("limit", "60"), ("q", "")]),
            req("Dataset: delete images and retrain", "POST", "dataset/delete", _json_body({"ids": ["PUT_IDS_FROM_GET_DATASET"]}),
                events=save_job, desc="Returns a job; poll Training job status."),
            req("Dataset: change a caption", "POST", "dataset/PUT_ID/caption", _json_body({"caption": "red sunset sky"}), events=save_job),
        ]}


def main(argv=None):
    out = (argv or sys.argv[1:] or ["api"])[0]
    os.makedirs(out, exist_ok=True)
    for name, obj in (("openapi.json", openapi()), ("postman_collection.json", postman_collection())):
        with open(os.path.join(out, name), "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        print("wrote", os.path.join(out, name))


if __name__ == "__main__":
    main()
