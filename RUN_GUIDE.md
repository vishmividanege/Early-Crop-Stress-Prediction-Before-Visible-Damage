# How to Run the Crop Stress Prediction Dashboard

This project consists of a Python FastAPI backend and a React Vite frontend.

## Prerequisites

- **Python 3.8+**
- **Node.js 16+** & **npm**
- **Google Earth Engine Account**: You need access to Google Earth Engine.

## 1. Backend Setup (FastAPI)

1.  Navigate to the backend directory:
    ```bash
    cd crop-stress-dashboard/backend
    ```

2.  (Optional but recommended) Create and activate a virtual environment:
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4.  Authenticate with Google Earth Engine:
    Run the following command and follow the instructions in the browser to copy the authentication code.
    ```bash
    earthengine authenticate
    ```

5.  Start the backend server:
    ```bash
    uvicorn app:app --reload
    ```
    The backend will run at `http://127.0.0.1:8000`.

## 2. Frontend Setup (React + Vite)

1.  Open a new terminal and navigate to the frontend directory:
    ```bash
    cd crop-stress-dashboard/frontend
    ```

2.  Install dependencies:
    ```bash
    npm install
    ```

3.  Start the development server:
    ```bash
    npm run dev
    ```
    The frontend will run at `http://localhost:5173`.

## 3. Usage

1.  Open your browser and verify the backend docs at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
2.  Open the frontend application at [http://localhost:5173](http://localhost:5173).
3.  Draw a polygon on the map to analyze crop stress in that area.

## Troubleshooting

- **Earth Engine Error**: If you see authentication errors in the backend console, ensure you ran `earthengine authenticate` and that your project ID `just-student-485912-k1` (hardcoded in `app.py`) is valid and accessible by your account.
- **CORS Error**: If the frontend cannot communicate with the backend, check the browser console. Ensure the backend is running on port 8000.
