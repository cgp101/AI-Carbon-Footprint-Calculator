# 🚀 Quick Setup Guide

## Step 1: Install Python
- Download Python 3.8+ from https://python.org/downloads/
- ✅ **Important**: Check "Add Python to PATH" during Windows installation

## Step 2: Clone & Setup Project
```bash
# Navigate to your desired directory
cd Desktop

# Clone the project (or download ZIP)
git clone <your-repo-url>
cd carbon-footprint-calculator

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate

```

## Step 3: Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt
```

## Step 4: Basic Configuration
The app works out-of-the-box with mock data. For full functionality:

**Optional: Azure OpenAI Setup (for photo upload)**
1. Edit `.venv/config.py`
2. Update your Azure OpenAI credentials:
   ```python
   AZURE_OPENAI_ENDPOINT = "your-endpoint"
   AZURE_OPENAI_API_KEY = "your-api-key"
   AZURE_OPENAI_DEPLOYMENT_NAME = "your-deployment"
   ```

## Step 5: Run the Application
```bash
# Start the app
cd .venv
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 🧪 Test the App

### **Manual Entry Test:**
1. Go to "✍️ Manual Entry"
2. Try: `"I drove 50 km and ate 2 restaurant meals"`
3. Click "Process Text"

### **Photo Upload Test:**
1. Go to "📸 Photo Upload" 
2. Upload any receipt/bill image
3. Click "Analyze with AI"

### **Analytics Test:**
1. Add a few entries
2. Go to "📈 Analytics"
3. View your carbon footprint trends

## 🛠️ Troubleshooting

### **Common Issues:**

**"Module not found" errors:**
```bash
pip install -r requirements.txt
```

**"Streamlit not found":**
```bash
pip install streamlit
```

**Azure OpenAI not working:**
- Check your configuration in `.venv/config.py`
- Verify your API key and endpoint
- The app works without Azure OpenAI (uses mock data)

**Database errors:**
```bash
# Reset database
rm .venv/carbon_footprint.db
```

**Port already in use:**
```bash
# Use different port
streamlit run app.py --server.port 8502
```

## 📁 File Structure
```
carbon-footprint-calculator/
├── .venv/               # Main application files
│   ├── app.py          # Streamlit web app
│   ├── config.py       # Configuration
│   └── ...             # Other modules
├── requirements.txt    # Dependencies
├── README.md          # Documentation
└── setup_guide.md     # This guide
```

## 🎯 Quick Start Commands
```bash
# Complete setup in one go:
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
cd .venv
streamlit run app.py
```

## ✅ Success Indicators
- App opens in browser
- Dashboard shows carbon footprint interface
- Manual entry accepts text input
- Analytics page displays charts
- No error messages in terminal

## 🔗 Next Steps
1. **Add entries**: Try manual entry with natural language
2. **Upload images**: Test photo upload with receipts
3. **View analytics**: Check your carbon footprint trends
4. **Explore features**: Try all tabs and functionality
5. **Customize**: Modify emission factors for your region

---

**Need help? Check the README.md for detailed documentation and troubleshooting.** 