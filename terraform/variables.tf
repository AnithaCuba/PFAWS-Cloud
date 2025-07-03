variable "aws_region" {
  description = "Región de AWS"
  type        = string
  default     = "us-east-1"
}

variable "input_bucket_name" {
  description = "Nombre del bucket S3 de entrada"
  type        = string
  
}

variable "output_bucket_name" {
  description = "Nombre del bucket S3 de salida"
  type        = string

}

variable "lambda_function_name" {
  description = "Nombre de la función Lambda"
  type        = string

}