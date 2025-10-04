import torch
from torchvision import transforms
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
import cv2
import os

this_path = os.path.dirname(os.path.abspath(__file__))
class CNN_Model(nn.Module):
    def __init__(self):
        super(CNN_Model, self).__init__()

        # Define layers
        self.conv1 = nn.Conv2d(3, 64, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(128, 256, kernel_size=3, padding=1)

        self.pool = nn.MaxPool2d(2, 2)
        self.flatten = nn.Flatten()
        self.fc1 = nn.Linear(256 * 16 * 16, 512)  # 256 channels * 16x16 (assuming image size 128x128)
        self.fc2 = nn.Linear(512, 7)  # 7 output classes (emotion categories)
        self.dropout = nn.Dropout(0.7)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = self.pool(x)
        x = F.relu(self.conv2(x))
        x = self.pool(x)
        x = F.relu(self.conv3(x))
        x = self.pool(x)

        x = self.flatten(x)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)

        return x

def load_model(model_path, device):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file tidak ditemukan di path: {model_path}")
    model = CNN_Model()
    #model.load_state_dict(torch.load(model_path))
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    return model

def prepare_image(image_path, device, transform):
    #image = Image.open(image_path)
    frame_rgb = cv2.cvtColor(image_path, cv2.COLOR_BGR2RGB)
    # Convert to PIL Image
    image = Image.fromarray(frame_rgb)
    image = transform(image).unsqueeze(0)
    image = image.to(device)
    return image

def predict(image, model, class_names):
    with torch.no_grad():
        output = model(image)
    probabilities = F.softmax(output, dim=1)
    _, predicted_class = torch.max(probabilities, 1)
    predicted_class_name = class_names[predicted_class.item()]
    
    prob_dict = {}
    for i, prob in enumerate(probabilities[0]):
        #prob_dict[class_names[i]] = prob.item() * 100
        prob_dict[class_names[i]] = round(prob.item() * 100, 4)
    
    prob_dict['predicted_class_name'] = predicted_class_name
    
    return predicted_class_name, prob_dict


def prediksi_cnn(image_path):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    #model_path = 'model/model_cnn.pth'
    model_path = os.path.join(this_path, "model", "model_cnn.pth")
    transform = transforms.Compose([
        transforms.Resize((128, 128)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
    ])
    model = load_model(model_path, device)
    class_names = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']

    image = prepare_image(image_path, device, transform)
    predicted_class_name, prob_dict = predict(image, model, class_names)    
    print(prob_dict)
    return predicted_class_name



