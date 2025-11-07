"""Main entry point for latent encoder service."""
import argparse
import sys
from pathlib import Path

from config import Config
from service import encode_image_to_latent
from kafka_handler import consume_and_process


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Latent Encoder Microservice")
    parser.add_argument(
        '--mode',
        choices=['standalone', 'kafka'],
        default=Config.mode,
        help='Service mode: standalone or kafka'
    )
    
    # Standalone mode arguments
    parser.add_argument('--image_path', help='Path to input image (for standalone mode)')
    parser.add_argument('--vae_model_name', default=Config.vae_model_name, help='VAE model name')
    parser.add_argument('--output_dir', default=Config.output_dir, help='Output directory')
    parser.add_argument('--upscale_method', default=Config.upscale_method, help='Upscale method')
    parser.add_argument('--megapixels', type=float, default=Config.megapixels, help='Target megapixels')
    parser.add_argument('--request_id', help='Request ID (auto-generated if not provided)')
    parser.add_argument('--no-save', action='store_true', help='Do not save tensor, return it instead')
    
    args = parser.parse_args()
    
    if args.mode == 'standalone':
        if not args.image_path:
            print("Error: --image_path is required for standalone mode")
            sys.exit(1)
        
        print(f"Encoding image: {args.image_path}")
        print(f"VAE Model: {args.vae_model_name}")
        print(f"Output Directory: {args.output_dir}")
        print("=" * 50)
        
        result = encode_image_to_latent(
            image_path=args.image_path,
            vae_model_name=args.vae_model_name,
            output_dir=args.output_dir,
            upscale_method=args.upscale_method,
            megapixels=args.megapixels,
            request_id=args.request_id,
            save_tensor=not args.no_save
        )
        
        print("\n" + "=" * 50)
        print("Result:")
        print(f"Status: {result['status']}")
        print(f"Request ID: {result['request_id']}")
        
        if result['status'] == 'success':
            if result.get('latent_file_path'):
                print(f"Latent saved to: {result['latent_file_path']}")
            if result.get('latent_shape'):
                print(f"Latent shape: {result['latent_shape']}")
            if result.get('latent_tensor') is not None:
                print(f"Latent tensor: {result['latent_tensor']}")
                print(f"Tensor shape: {result['latent_tensor'].shape}")
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



