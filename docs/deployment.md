# GajaAlert AI - Deployment Guide & Infrastructure Notes

This document details deployment strategies for GajaAlert AI, spanning Docker containerization, Gunicorn WSGI production configuration, systemd service installation, and edge deployment notes.

---

## 1. Docker Deployment

### Building the Docker Image
```bash
docker build -t gajaalert-ai:latest .
```

### Running the Container
```bash
docker run -d \
  --name gajaalert \
  -p 5000:5000 \
  -v $(pwd)/gajaalert.db:/app/gajaalert.db \
  -v $(pwd)/model:/app/model \
  -v $(pwd)/static/uploads:/app/static/uploads \
  gajaalert-ai:latest
```

### Verifying Container Health
```bash
docker ps
curl http://localhost:5000/health
```

---

## 2. Linux Production Server Deployment (Gunicorn + Systemd)

### Systemd Service File (`/etc/systemd/system/gajaalert.service`)
```ini
[Unit]
Description=GajaAlert AI Early Warning Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/gajaalert
Environment="PATH=/opt/gajaalert/venv/bin"
ExecStart=/opt/gajaalert/venv/bin/gunicorn --workers 2 --threads 2 --bind 127.0.0.1:5000 app:app

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Enabling and Starting the Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable gajaalert
sudo systemctl start gajaalert
sudo systemctl status gajaalert
```

---

## 3. Nginx Reverse Proxy & SSL Configuration

### Nginx Site Configuration (`/etc/nginx/sites-available/gajaalert`)
```nginx
server {
    listen 80;
    server_name gajaalert.local;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/gajaalert/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
}
```

---

## 4. Edge Hardware Deployment Notes (Raspberry Pi / ESP32-CAM)

1. **TensorFlow Lite Conversion**:
   Convert `.keras` model to quantized `.tflite` format for edge microcontrollers:
   ```python
   import tensorflow as tf
   converter = tf.lite.TFLiteConverter.from_keras_model(model)
   converter.optimizations = [tf.lite.Optimize.DEFAULT]
   tflite_model = converter.convert()
   with open('model/gajaalert_model.tflite', 'wb') as f:
       f.write(tflite_model)
   ```

2. **Camera Node Sync**:
   Field ESP32-CAM camera trap nodes send captured frames over MQTT or HTTPS POST to `/predict`.
