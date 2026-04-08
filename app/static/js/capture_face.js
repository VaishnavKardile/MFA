const video = document.getElementById('webcam');
const canvas = document.getElementById('canvas');
const captureBtn = document.getElementById('captureBtn');
const imageInput = document.getElementById('image_data');
const faceForm = document.getElementById('faceForm');

// 1. Ask the browser for permission to use the webcam
navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        video.srcObject = stream;
    })
    .catch(err => {
        console.error("Camera access denied:", err);
        alert("Please allow camera access in your browser to continue.");
    });

// 2. When the user clicks the capture button
captureBtn.addEventListener('click', () => {
    // Set the hidden canvas to the same size as the video feed
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Draw the current video frame onto the canvas
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convert that picture into a base64 string
    const dataURL = canvas.toDataURL('image/jpeg');
    
    // Put the string into our hidden form field
    imageInput.value = dataURL;
    
    // Submit the form to your Python routes.py
    faceForm.submit();
});