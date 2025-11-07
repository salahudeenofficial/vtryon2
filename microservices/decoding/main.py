"""Main entry point for decoding service."""
import argparse
import sys
from pathlib import Path

from config import Config
from service import decode_latent_to_image
from kafka_handler import consume_and_process


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Decoding Microservice")
    parser.add_argument(
        '--mode',
        choices=['standalone', 'kafka'],
        default=Config.mode,
        help='Service mode: standalone or kafka'
    )
    
    # Standalone mode arguments
    parser.add_argument('--latent', help='Path to latent .pt file (for standalone mode)')
    parser.add_argument('--vae_model_name', default=Config.vae_model_name, help='VAE model name')
    parser.add_argument('--output_filename', default="output", help='Base name for output image file')
    parser.add_argument('--output_dir', default=Config.output_dir, help='Output directory')
    parser.add_argument('--output_format', default=Config.default_output_format, choices=['jpg', 'jpeg', 'png', 'webp'], help='Output image format')
    parser.add_argument('--request_id', help='Request ID (auto-generated if not provided)')
    parser.add_argument('--no-save', action='store_true', help='Do not save image, return tensor instead')
    
    args = parser.parse_args()
    
    if args.mode == 'standalone':
        if not args.latent:
            print("Error: --latent is required for standalone mode")
            sys.exit(1)
        
        print(f"Decoding latent to image:")
        print(f"  Latent: {args.latent}")
        print(f"  VAE Model: {args.vae_model_name}")
        print(f"  Output Filename: {args.output_filename}")
        print(f"  Output Directory: {args.output_dir}")
        print(f"  Output Format: {args.output_format}")
        print("=" * 50)
        
        result = decode_latent_to_image(
            latent=args.latent,
            vae_model_name=args.vae_model_name,
            output_filename=args.output_filename,
            output_dir=args.output_dir,
            output_format=args.output_format,
            request_id=args.request_id,
            save_image=not args.no_save
        )
        
        print("\n" + "=" * 50)
        print("Result:")
        print(f"Status: {result['status']}")
        print(f"Request ID: {result['request_id']}")
        
        if result['status'] == 'success':
            if result.get('image_file_path'):
                print(f"Image saved to: {result['image_file_path']}")
            if result.get('image_shape'):
                print(f"Image shape: {result['image_shape']}")
            if result.get('file_size'):
                print(f"File size: {result['file_size']} bytes")
            if result.get('image_tensor') is not None:
                print(f"Image tensor shape: {result['image_tensor'].shape}")
            if result.get('metadata'):
                print(f"Processing time: {result['metadata'].get('processing_time_ms')}ms")
        else:
            print(f"Error Code: {result.get('error_code')}")
            print(f"Error Message: {result.get('error_message')}")
            sys.exit(1)
        
    elif args.mode == 'kafka':
        print("Starting Kafka consumer...")
        print(f"Bootstrap Servers: {Config.kafka_bootstrap_servers}")
        print(f"Request Topic: {Config.kafka_request_topic}")
        print(f"Response Topic: {Config.kafka_response_topic}")
        print(f"Consumer Group: {Config.kafka_consumer_group}")
        consume_and_process()


if __name__ == "__main__":
    main()



