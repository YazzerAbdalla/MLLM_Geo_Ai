"""
 * Unified training script for all models.
 *
 * Usage:
 *   python scripts/train.py --model baseline      # Train Random Forest only
 *   python scripts/train.py --model multimodal   # Train UrbanMLP only
 *   python scripts/train.py --model all          # Train both (default)
 """
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    parser = argparse.ArgumentParser(description="Train ML models")
    parser.add_argument(
        "--model",
        choices=["baseline", "multimodal", "all"],
        default="all",
        help="Which model to train (default: all)"
    )
    args = parser.parse_args()

    if args.model in ["baseline", "all"]:
        print("=" * 50)
        print("Training baseline (Random Forest)...")
        print("=" * 50)
        from scripts.train_baseline import train as train_baseline
        train_baseline()

    if args.model in ["multimodal", "all"]:
        print("=" * 50)
        print("Training multimodal (UrbanMLP)...")
        print("=" * 50)
        from scripts.train_multimodal import train as train_multimodal
        train_multimodal()

    print("=" * 50)
    print("Training complete!")
    print("=" * 50)

    if os.path.exists("models/random_forest.pkl") and os.path.exists("models/urban_mlp.pt"):
        print("\nModels saved:")
        print("  - models/random_forest.pkl")
        print("  - models/urban_mlp.pt")


if __name__ == "__main__":
    main()