# Functional Connectivity Website

This project is a web application for analyzing and visualizing functional connectivity in brain imaging data. It provides tools for processing NIfTI files and generating connectivity matrices using a Graph Convolutional Network (GCN) model.

## Features

- NIfTI file processing and analysis
- Functional connectivity matrix generation
- Interactive visualization of brain connectivity
- Graph Convolutional Network (GCN) based connectivity analysis
- Support for Harvard-Oxford subcortical atlas

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   └── model_processor.py
│   └── models/
├── frontend/
│   ├── public/
│   ├── src/
│   └── package.json
└── README.md
```

## Setup and Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
cd functional-connectivity-website
```

2. Set up the backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up the frontend:
```bash
cd frontend
npm install
```

## Running the Application

1. Start the backend server:
```bash
cd backend
python app.py
```

2. Start the frontend development server:
```bash
cd frontend
npm start
```

## Dependencies

### Backend
- Python 3.x
- NumPy
- Nibabel
- Nilearn
- PyTorch
- PyTorch Geometric

### Frontend
- React
- Node.js
- npm

## License

[Your chosen license]

## Contributing

[Your contribution guidelines] 