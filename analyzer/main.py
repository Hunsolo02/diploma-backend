# train_landmarks.py
import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
import torch.optim as optim
from tqdm import tqdm

from datasetFace import FaceLandmarkDataset
from model import LandmarkModel  # лучше держать модель в model.py


# ====== Параметры ======
json_path = "/home/ermakov/webproj/trainModel2/huggingface_landmarks.json"
save_path = "/home/ermakov/webproj/trainModel2/landmark_model.pth"

IMG_SIZE = 128
BATCH_SIZE = 64
EPOCHS = 60
LR = 1e-4
WEIGHT_DECAY = 1e-4
SEED = 42


def set_seed(seed: int):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def main():
    set_seed(SEED)

    device = "cuda" if torch.cuda.is_available() else "cpu"

    print("✅ Загрузка датасета (HF + landmarks [0..1])...")
    # Вариант 1: датасет читает картинки из HF по hf_index, image_dir не нужен
    dataset = FaceLandmarkDataset(json_path, img_size=IMG_SIZE)

    # Лучше брать num_points из метаданных датасета, а не через dataset[0]
    num_points = getattr(dataset, "num_points", None)
    if num_points is None:
        num_points = len(dataset[0][1]) // 2
    print("🔢 num_points:", num_points, "| output dims:", num_points * 2)

    # split train/val (80/20)
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = random_split(dataset, [train_size, val_size])

    print(f"📊 Размеры: train={len(train_dataset)}, val={len(val_dataset)}")

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=4,
        pin_memory=True
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=4,
        pin_memory=True
    )

    # ====== Модель ======
    model = LandmarkModel(num_points).to(device)

    # ✅ Раз landmarks нормализованные [0..1], выход модели тоже должен быть [0..1]
    # Самый простой способ: сигмоида на выход
    # Если в LandmarkModel уже есть Sigmoid — эту строку не надо.
    if not hasattr(model, "has_sigmoid_head"):
        # Не трогаем архитектуру внутри, просто оборачиваем выход
        model = nn.Sequential(model, nn.Sigmoid()).to(device)

    # Loss: SmoothL1 устойчивее, чем MSE для координат
    criterion = nn.SmoothL1Loss(beta=0.01)

    optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)

    # Scheduler (не обязателен, но помогает)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=4
    )

    best_val = float("inf")

    print("🚀 Начинается обучение...\n")
    for epoch in range(EPOCHS):
        model.train()
        total_loss = 0.0

        pbar = tqdm(train_loader, desc=f"🏋️ Train {epoch+1}/{EPOCHS}", leave=False)
        for images, landmarks in pbar:
            images = images.to(device, non_blocking=True)
            landmarks = landmarks.to(device, non_blocking=True)

            preds = model(images)
            loss = criterion(preds, landmarks)

            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            total_loss += float(loss.item())
            pbar.set_postfix(loss=float(loss.item()), lr=optimizer.param_groups[0]["lr"])

        avg_train_loss = total_loss / max(1, len(train_loader))

        # ====== Валидация ======
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for images, landmarks in val_loader:
                images = images.to(device, non_blocking=True)
                landmarks = landmarks.to(device, non_blocking=True)

                preds = model(images)
                loss = criterion(preds, landmarks)
                val_loss += float(loss.item())

        avg_val_loss = val_loss / max(1, len(val_loader))
        scheduler.step(avg_val_loss)

        print(f"📉 Epoch {epoch+1}/{EPOCHS}: Train={avg_train_loss:.6f} | Val={avg_val_loss:.6f}")

        # ====== Save best ======
        if avg_val_loss < best_val:
            best_val = avg_val_loss
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            # если модель обёрнута Sequential(model, Sigmoid), сохраним "сырую" часть тоже:
            state_to_save = model.state_dict()
            torch.save(state_to_save, save_path)
            print(f"✅ Best model saved: {save_path} (val={best_val:.6f})")

    print("🏁 Training finished.")
    print("✅ Final best val:", best_val)


if __name__ == "__main__":
    main()
