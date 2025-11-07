"""Main entry point for text encoder service."""
import argparse
import sys
from pathlib import Path

from config import Config
from service import encode_text_and_images
from kafka_handler import consume_and_process


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Text Encoder Microservice")
    parser.add_argument(
        '--mode',
        choices=['standalone', 'kafka'],
        default=Config.mode,
        help='Service mode: standalone or kafka'
    )
    
    # Standalone mode arguments
    parser.add_argument('--image1_path', help='Path to first image (masked person - for standalone mode)')
    parser.add_argument('--image2_path', help='Path to second image (cloth - for standalone mode)')
    parser.add_argument('--prompt', help='Text prompt for positive conditioning (for standalone mode)')
    parser.add_argument('--negative_prompt', default="", help='Text prompt for negative conditioning (default: "")')
    parser.add_argument('--clip_model_name', default=Config.clip_model_name, help='CLIP model name')
    parser.add_argument('--vae_model_name', default=Config.vae_model_name, help='VAE model name')
    parser.add_argument('--output_dir', default=Config.output_dir, help='Output directory')
    parser.add_argument('--upscale_method', default=Config.upscale_method, help='Upscale method')
    parser.add_argument('--megapixels', type=float, default=Config.megapixels, help='Target megapixels')
    parser.add_argument('--request_id', help='Request ID (auto-generated if not provided)')
    parser.add_argument('--no-save', action='store_true', help='Do not save tensors, return them instead')
    
    args = parser.parse_args()
    
    if args.mode == 'standalone':
        if not args.image1_path:
            print("Error: --image1_path is required for standalone mode")
            sys.exit(1)
        if not args.image2_path:
            print("Error: --image2_path is required for standalone mode")
            sys.exit(1)
        if not args.prompt:
            print("Error: --prompt is required for standalone mode")
            sys.exit(1)
        
        print(f"Encoding text and images:")
        print(f"  Image1: {args.image1_path}")
        print(f"  Image2: {args.image2_path}")
        print(f"  Prompt: {args.prompt}")
        print(f"  Negative Prompt: {args.negative_prompt}")
        print(f"  CLIP Model: {args.clip_model_name}")
        print(f"  VAE Model: {args.vae_model_name}")
        print(f"  Output Directory: {args.output_dir}")
        print("=" * 50)
        
        result = encode_text_and_images(
            image1_path=args.image1_path,
            image2_path=args.image2_path,
            prompt=args.prompt,
            negative_prompt=args.negative_prompt,
            clip_model_name=args.clip_model_name,
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
            if result.get('positive_encoding_file_path'):
                print(f"Positive encoding saved to: {result['positive_encoding_file_path']}")
            if result.get('negative_encoding_file_path'):
                print(f"Negative encoding saved to: {result['negative_encoding_file_path']}")
            if result.get('positive_encoding_shape'):
                print(f"Positive encoding shape: {result['positive_encoding_shape']}")
            if result.get('negative_encoding_shape'):
                print(f"Negative encoding shape: {result['negative_encoding_shape']}")
            if result.get('positive_encoding_tensor') is not None:
                print(f"Positive tensor shape: {result['positive_encoding_tensor'].shape}")
            if result.get('negative_encoding_tensor') is not None:
                print(f"Negative tensor shape: {result['negative_encoding_tensor'].shape}")
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



