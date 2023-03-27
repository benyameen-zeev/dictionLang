from google.cloud import translate_v2 as translate

translate_client = translate.Client()

text = "Hello, world!"
target_language = "fr"

result = translate_client.translate(
    text,
    target_language=target_language
)

translated_text = result["translatedText"]
print(translated_text)
