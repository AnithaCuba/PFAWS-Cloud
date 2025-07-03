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
    # 20 reglas 
    try:
        # Regla ID numérico positivo y solo dígitos
        if not str(row.get('id', '')).isdigit():
            return None
        row['id'] = int(row['id'])
        if row['id'] <= 0:
            return None
    except:
        return None

    # Regla Campos críticos no nulos
    if not row.get('fecha_not') or not row.get('clasificacion'):
        return None

    # Regla Mayusculas en campos clave
    for key in ['diresa', 'red', 'microred', 'establecimiento', 'institucion', 'clasificacion']:
        if row.get(key):
            row[key] = row[key].strip().upper()

    # Regla Valor por defecto para asintomático
    row['asintomatico'] = row.get('asintomatico', 'NO ESPECIFICADO').strip().upper()
    if not row['asintomatico']:
        row['asintomatico'] = "NO"

    # Regla Validar y formatear fecha (MM/DD/YYYY a YYYY-MM-DD), fecha no futura ni antes 2015
    try:
        fecha = datetime.strptime(row['fecha_not'], "%m/%d/%Y")
        if fecha > datetime.now() or fecha.year < 2015:
            return None
        row['fecha_not'] = fecha.strftime("%Y-%m-%d")
    except:
        return None

    # Regla Año y semana como enteros
    try:
        row['ano'] = int(row['ano'])
        row['semana'] = int(row['semana'])
    except:
        return None

    # Regla Semana válida (1–53)
    if row['semana'] < 1 or row['semana'] > 53:
        return None

    # Regla Clasificación permitida
    if row['clasificacion'] not in ['CONFIRMADO', 'DESCARTADO', 'SOSPECHOSO']:
        return None

    # Regla Limpiar espacios extras en 'institucion'
    if row.get('institucion'):
        row['institucion'] = ' '.join(row['institucion'].split())

    # Regla Excluir establecimiento inválido (que contenga 'SIN DATO')
    if "SIN DATO" in row.get('establecimiento', ''):
        return None

    # Regla Crear campo anio_semana con formato AAAA-Sww
    row['anio_semana'] = f"{row['ano']}-S{str(row['semana']).zfill(2)}"

    # Regla Eliminar comillas y caracteres especiales solo alfanum y espacios en campos clave
    for key in ['microred', 'establecimiento', 'diresa', 'red']:
        value = row.get(key, '')
        value = value.replace('"', '').replace("'", "")
        value = ''.join(e for e in value if e.isalnum() or e.isspace())
        row[key] = value.strip()

    # Regla Validar institución contra lista ampliada (de tu data real)
    instituciones_validas = [
        'MINSA', 'ESSALUD','PNP', 'PRIVADO', 'GOBIERNO REGIONAL', 'SANIDAD DE LA POLICIA NACIONAL DEL PERU'
    ]
    if row.get('institucion') not in instituciones_validas:
        return None

    # Regla Normalizar campos a Título (Primera letra mayúscula)
    for key in ['diresa', 'red', 'microred']:
        if row.get(key):
            row[key] = row[key].title()

    # Regla Validar año entre 2020 y 2025
    if row['ano'] < 2020 or row['ano'] > 2025:
        return None

    # Regla Crear clave única para eliminar duplicados
    row['unique_key'] = f"{row['id']}_{row['fecha_not']}"

    return row