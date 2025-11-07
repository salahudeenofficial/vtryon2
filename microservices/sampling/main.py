"""Main entry point for sampling service."""
import argparse
import sys
from pathlib import Path

from config import Config
from service import sample_latent
from kafka_handler import consume_and_process


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Sampling Microservice")
    parser.add_argument(
        '--mode',
        choices=['standalone', 'kafka'],
        default=Config.mode,
        help='Service mode: standalone or kafka'
    )
    
    # Standalone mode arguments
    parser.add_argument('--positive_encoding', help='Path to positive encoding .pt file (for standalone mode)')
    parser.add_argument('--negative_encoding', help='Path to negative encoding .pt file (for standalone mode)')
    parser.add_argument('--latent_image', help='Path to latent image .pt file (for standalone mode)')
    parser.add_argument('--unet_model_name', default=Config.unet_model_name, help='UNET model name')
    parser.add_argument('--lora_model_name', default=Config.lora_model_name, help='LoRA model name')
    parser.add_argument('--lora_strength', type=float, default=Config.lora_strength, help='LoRA strength')
    parser.add_argument('--seed', type=int, default=None, help='Random seed (None for random)')
    parser.add_argument('--steps', type=int, default=Config.default_steps, help='Number of sampling steps')
    parser.add_argument('--cfg', type=float, default=Config.default_cfg, help='CFG scale')
    parser.add_argument('--sampler_name', default=Config.default_sampler_name, help='Sampler name')
    parser.add_argument('--scheduler', default=Config.default_scheduler, help='Scheduler name')
    parser.add_argument('--denoise', type=float, default=Config.default_denoise, help='Denoise strength')
    parser.add_argument('--shift', type=int, default=Config.default_shift, help='AuraFlow shift')
    parser.add_argument('--strength', type=float, default=Config.default_strength, help='CFGNorm strength')
    parser.add_argument('--output_dir', default=Config.output_dir, help='Output directory')
    parser.add_argument('--request_id', help='Request ID (auto-generated if not provided)')
    parser.add_argument('--no-save', action='store_true', help='Do not save tensor, return it instead')
    
    args = parser.parse_args()
    
    if args.mode == 'standalone':
        if not args.positive_encoding:
            print("Error: --positive_encoding is required for standalone mode")
            sys.exit(1)
        if not args.negative_encoding:
            print("Error: --negative_encoding is required for standalone mode")
            sys.exit(1)
        if not args.latent_image:
            print("Error: --latent_image is required for standalone mode")
            sys.exit(1)
        
        print(f"Sampling latent:")
        print(f"  Positive Encoding: {args.positive_encoding}")
        print(f"  Negative Encoding: {args.negative_encoding}")
        print(f"  Latent Image: {args.latent_image}")
        print(f"  UNET Model: {args.unet_model_name}")
        print(f"  LoRA Model: {args.lora_model_name}")
        print(f"  LoRA Strength: {args.lora_strength}")
        print(f"  Seed: {args.seed if args.seed is not None else 'random'}")
        print(f"  Steps: {args.steps}")
        print(f"  CFG: {args.cfg}")
        print(f"  Sampler: {args.sampler_name}")
        print(f"  Scheduler: {args.scheduler}")
        print(f"  Denoise: {args.denoise}")
        print(f"  Shift: {args.shift}")
        print(f"  Strength: {args.strength}")
        print(f"  Output Directory: {args.output_dir}")
        print("=" * 50)
        
        result = sample_latent(
            positive_encoding=args.positive_encoding,
            negative_encoding=args.negative_encoding,
            latent_image=args.latent_image,
            unet_model_name=args.unet_model_name,
            lora_model_name=args.lora_model_name,
            lora_strength=args.lora_strength,
            seed=args.seed,
            steps=args.steps,
            cfg=args.cfg,
            sampler_name=args.sampler_name,
            scheduler=args.scheduler,
            denoise=args.denoise,
            shift=args.shift,
            strength=args.strength,
            output_dir=args.output_dir,
            request_id=args.request_id,
            save_tensor=not args.no_save
        )
        
        print("\n" + "=" * 50)
        print("Result:")
        print(f"Status: {result['status']}")
        print(f"Request ID: {result['request_id']}")
        
        if result['status'] == 'success':
            if result.get('sampled_latent_file_path'):
                print(f"Sampled latent saved to: {result['sampled_latent_file_path']}")
            if result.get('sampled_latent_shape'):
                print(f"Sampled latent shape: {result['sampled_latent_shape']}")
            if result.get('sampled_latent_tensor') is not None:
                print(f"Sampled tensor shape: {result['sampled_latent_tensor'].shape}")
            if result.get('metadata'):
                print(f"Processing time: {result['metadata'].get('processing_time_ms')}ms")
                print(f"Seed used: {result['metadata'].get('seed')}")
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



