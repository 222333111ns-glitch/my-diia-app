from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import aiosqlite
import os
import time

app = FastAPI()

@app.get("/get_data")
async def get_data(code: str = Query(...)):
    async with aiosqlite.connect("users.db") as db:
        async with db.execute("SELECT fio, birthdate, photo_path, expiry_time, active FROM users WHERE code=?", (code,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Код не знайдено")
            fio, birthdate, photo_path, expiry, active = row
            
            # Перевірка терміну дії та активності
            if active == 0 or (expiry and time.time() > expiry):
                return {
                    "fio": "ПЕРІОД ПОДПИСКИ ЗАВЕРШЕНО",
                    "birthdate": "",
                    "photo_url": ""
                }
            
            photo_url = f"/photos/{os.path.basename(photo_path)}" if photo_path else ""
            return {
                "fio": fio or "Дані не знайдено",
                "birthdate": birthdate or "",
                "photo_url": photo_url
            }

# Статичні файли (фото)
app.mount("/photos", StaticFiles(directory="photos"), name="photos")

# Головна сторінка PWA
@app.get("/", response_class=HTMLResponse)
async def main_page():
    return """
    <!DOCTYPE html>
    <html lang="uk">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Дія</title>
        <link rel="manifest" href="/manifest.json">
        <style>
            body { font-family: Arial, sans-serif; text-align: center; background: #fff; color: #000; padding: 20px; }
            h1 { font-size: 32px; }
            input { font-size: 18px; padding: 10px; width: 80%; margin: 20px; }
            button { font-size: 18px; padding: 12px 24px; background: #000; color: #ffd700; border: none; border-radius: 8px; }
            .data { margin-top: 40px; }
            img { max-width: 200px; border-radius: 12px; margin: 20px 0; }
            .expired { color: red; font-size: 24px; }
        </style>
    </head>
    <body>
        <h1>Аналог Дія</h1>
        <p>Введіть код доступу з бота:</p>
        <input type="text" id="code" placeholder="Наприклад: 8a85069d">
        <button onclick="loadData()">Увійти</button>
        
        <div id="result" class="data"></div>

        <script>
            async function loadData() {
                const code = document.getElementById('code').value.trim();
                if (!code) return alert("Введіть код!");
                
                try {
                    const res = await fetch(`/get_data?code=${code}`);
                    const data = await res.json();
                    
                    let html = '';
                    if (data.fio.includes("ЗАВЕРШЕНО")) {
                        html = `<p class="expired">${data.fio}</p>`;
                    } else {
                        html = `
                            <h2>Ваші дані</h2>
                            <p><strong>ПІБ:</strong> ${data.fio}</p>
                            <p><strong>Дата народження:</strong> ${data.birthdate}</p>
                            ${data.photo_url ? `<img src="${data.photo_url}" alt="Фото">` : ''}
                        `;
                    }
                    document.getElementById('result').innerHTML = html;
                } catch (e) {
                    alert("Невірний код або термін дії закінчився");
                }
            }
        </script>
    </body>
    </html>
    """