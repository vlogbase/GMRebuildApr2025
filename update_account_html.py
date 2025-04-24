#!/usr/bin/env python3

with open("templates/account.html", "r") as f:
    content = f.read()

# Replace both instances of multimodal property with multimodal and cost_band
updated_content = content.replace(
    "                        multimodal: modelDetails.is_multimodal ? 'Yes' : 'No'",
    "                        multimodal: modelDetails.is_multimodal ? 'Yes' : 'No',\n                        cost_band: modelDetails.cost_band || ''"
)

with open("templates/account.html", "w") as f:
    f.write(updated_content)

print("File updated successfully.")
