from transformers import AutoTokenizer, AutoModelForSequenceClassification
from huggingface_hub import hf_hub_download, list_repo_files
import torch
import requests

MODEL_NAME = "Pzzzzi/relation-classifier"

def verify_repo_files():
    print("🔄 Checking repository files...")
    try:
        files = list_repo_files(MODEL_NAME)
        required_files = {
            'config.json', 
            'tokenizer_config.json', 'vocab.json',
            'merges.txt', 'special_tokens_map.json'
        }
        
        missing = required_files - set(files)
        if missing:
            print(f"❌ Missing files: {missing}")
            return False
        
        print("✅ All required files present")
        return True
        
    except Exception as e:
        print(f"❌ Error checking repo: {str(e)}")
        return False

def verify_config():
    print("\n🔍 Verifying config.json...")
    try:
        config_url = f"https://huggingface.co/{MODEL_NAME}/raw/main/config.json"
        config = requests.get(config_url).json()
        
        # Check critical values
        assert config.get("model_type") == "roberta", "Wrong model_type"
        assert "RobertaForSequenceClassification" in config.get("architectures", []), "Wrong architecture"
        assert "id2label" in config, "Missing id2label"
        
        print("✅ Config verification passed")
        return True
        
    except Exception as e:
        print(f"❌ Config error: {str(e)}")
        return False

def load_model():
    if not verify_repo_files() or not verify_config():
        raise ValueError("Repository verification failed")
    
    print("\n🚀 Loading model...")
    try:
        # First try loading tokenizer separately
        print("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        print("✅ Tokenizer loaded")
        
        # Then try loading model
        print("Loading model...")
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
        print("✅ Model loaded")
        
        return tokenizer, model
        
    except Exception as e:
        print(f"\n❌ Load failed: {str(e)}")
        print("\nDebugging steps:")
        print("1. Check file sizes (pytorch_model.bin should be >100MB)")
        print("2. Verify transformers version compatibility")
        print(f"3. Test direct download: https://huggingface.co/{MODEL_NAME}")
        raise

def main():
    try:
        tokenizer, model = load_model()
        print("\n🎉 Model loaded successfully! Testing prediction...")
        
        # Test prediction
        test_text = "Apple [SEP] iPhone [SEP] Apple announced the new iPhone."
        inputs = tokenizer(test_text, return_tensors="pt", truncation=True)
        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.softmax(outputs.logits, dim=1)
        
        print(f"\nPrediction probabilities: {probs}")
        
    except Exception as e:
        print(f"\n💥 Final error: {str(e)}")

if __name__ == "__main__":
    main()