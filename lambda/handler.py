import boto3
import csv
import json
import os

s3 = boto3.client('s3')

def lambda_handler(event, context):
    # Obtener nombre de archivo
    bucket = event['Records'][0]['s3']['bucket']['name']
    key    = event['Records'][0]['s3']['object']['key']

    if not key.endswith('.csv'):
        print("Archivo no es CSV. Se ignora.")
        return

    response = s3.get_object(Bucket=bucket, Key=key)
    lines = response['Body'].read().decode('utf-8').splitlines()

    reader = csv.DictReader(lines)
    cleaned_data = []

    for row in reader:
        cleaned_row = aplicar_reglas(row)  # <- función personalizada
        cleaned_data.append(cleaned_row)

    output_bucket = os.environ.get("OUTPUT_BUCKET_NAME")
    output_key = key.replace(".csv", ".json")

    s3.put_object(
        Bucket=output_bucket,
        Key=output_key,
        Body=json.dumps(cleaned_data),
        ContentType='application/json'
    )

def aplicar_reglas(row):
    # Aplica tus 20 reglas aquí
    # Ejemplo:
    row['pais'] = row['pais'].strip().title()
    row['casos'] = int(row['casos']) if row['casos'].isdigit() else 0
    # ... continúa con tus otras 18 reglas ...
    return row