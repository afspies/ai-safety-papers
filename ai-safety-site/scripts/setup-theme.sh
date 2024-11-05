#!/bin/bash

# Create necessary directories
mkdir -p themes/hugo-theme-monochrome/assets/lib/js/
mkdir -p themes/hugo-theme-monochrome/assets/feather-sprite/

# Download required JS files
curl -L https://cdn.jsdelivr.net/npm/uFuzzy@1.0.14/dist/uFuzzy.esm.js -o themes/hugo-theme-monochrome/assets/lib/js/uFuzzy-v1.0.14.esm.js
curl -L https://cdn.jsdelivr.net/npm/zooming@2.1.1/build/zooming.min.js -o themes/hugo-theme-monochrome/assets/lib/js/zooming-v2.1.1.min.js

# Download feather icons sprite
curl -L https://unpkg.com/feather-icons@4.29.0/dist/feather-sprite.svg -o themes/hugo-theme-monochrome/assets/feather-sprite/feather-sprite.svg 