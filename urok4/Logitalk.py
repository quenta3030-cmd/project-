import base64
import io
import threading
from PIL import Image

from customtkinter import *
from socket import *

class MainWindow(CTk):
    def __init__(self):
        super().__init__()
        self.geometry("400x300")
        self.title("win")

        self.menu_frame = CTkFrame(self, width=30,height=300, fg_color="#1E1C1C")
        self.menu_frame.pack_propagate(False)
        self.menu_frame.place(x=0,y=0)

        self.is_show_menu = False
        self.speed_anim_menu = -5


        self.btn = CTkButton(self, text='▶️', command=self.toggle_show_menu, width=30)
        self.btn.place(x=0, y=0)


        self.message_entry = CTkEntry(self, placeholder_text="Введіть текст",  height=40)
        self.message_entry.place(x=0, y=40)


        self.send_btn = CTkButton(self, text='>', width=30, height=40,command=self.send_message)
        self.send_btn.place(x=0, y=50)

        self.bg_image = CTkImage(light_image=Image.open("img.png"), size=(30, 30))
        self.open_img_button = CTkButton(self, text='', width=50, height=40, command=self.open_image,
                                         image=self.bg_image)
        self.open_img_button.place(x=0, y=0)

        self.chat_field = CTkScrollableFrame(self)

        self.chat_field.place(x=0, y=100)



        # Запускаємо адаптивне компонування
        self.adaptive_ui()
        self.bind("<Return>",lambda e: self.send_message())

        self.username = 'Andrew'
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect(('4.tcp.ngrok.io', 14565))
            hello = f"TEXT@{self.username}@[SYSTEM] {self.username} приєднався(лась) до чату!\n"
            self.sock.send(hello.encode('utf-8'))
            threading.Thread(target=self.recv_message, daemon=True).start()
        except Exception as e:
            self.add_message(f"Не вдалося підключитися до сервера: {e}")
        # new


    # --- ЛОГІКА ПЕРЕМИКАННЯ МЕНЮ ---
    def toggle_show_menu(self):
        if self. is_show_menu:
            self.is_show_menu = False
            self.speed_anim_menu *= -1
            self.btn.configure(text="▶")
            self.show_menu()
        else:
            self.is_show_menu = True
            self.speed_anim_menu *= -1
            self.btn.configure(text="◀")
            self.show_menu()

            self.label=CTkLabel(self.menu_frame, text="Ваше ім'я")
            self.label.pack(pady=30)

            self.entry = CTkEntry(self.menu_frame)
            self.entry.pack()

            self.save_button = CTkButton(self.menu_frame, text="Зберегти ім'я",command=self.save_name)
            self.save_button.pack()


    # --- АНІМАЦІЯ ВІДКРИТТЯ/ЗАКРИТТЯ МЕНЮ ---
    def show_menu(self):
        self.menu_frame.configure(width=self.menu_frame.winfo_width() + self.speed_anim_menu)
        if not self.menu_frame.winfo_width() >= 200 and self.is_show_menu:
            self.after(10, self.show_menu)
        elif self.menu_frame.winfo_width() >= 40 and not self.is_show_menu:
            self.after(10, self.show_menu)
            # Видаляємо внутрішні віджети, коли меню згортається
            if self.label:
                self.label.destroy()
            if getattr(self, "entry", None):
                self.entry.destroy()
            if getattr(self, "save_button", None):
                self.save_button.destroy()

    def save_name(self):
        new_name = self.entry.get().strip()
        if new_name:
            self.username = new_name
            self.add_message(f"ваш новий нік: '{self.username}'")





    def add_message(self, message, img=None, anchor="w"):
        message_frame = CTkFrame(self.chat_field, fg_color='grey')
        message_frame.pack(pady=5, anchor=anchor)
        wrapleng_size = self.winfo_width() - self.menu_frame.winfo_width() - 40

        if not img:
            CTkLabel(message_frame, text=message, wraplength=wrapleng_size, text_color='white', justify='left').pack(
                padx=10, pady=5)
        else:
            CTkLabel(message_frame, text=message, wraplength=wrapleng_size, text_color='white', image=img, compound='top',
                     justify='left').pack(padx=10, pady=5)
        row = CTkFrame(message_frame, fg_color="transparent")
        row.pack(anchor='w', fill='x')



    def send_message(self):
        message = self.message_entry.get()
        if message:
            self.add_message(f"{self.username}: {message}")
            data = f"TEXT@{self.username}@{message}\n"
            try:
                self.sock.sendall(data.encode())
            except:
                self.add_message("Помилка відправленя ")
        self.message_entry.delete(0, END)

    def recv_message(self):
        buffer = ""
        while True:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk.decode('utf-8', errors='ignore')

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.handle_line(line.strip())

            except:
                break
        self.sock.close()

    def handle_line(self, line):
        if not line:
            return
        parts = line.split("@", 3)
        msg_type = parts[0]

        if msg_type == "TEXT":
            author = parts[1]
            message = parts[2]
            self.add_message(f"{author}: {message}",anchor="e")

        elif msg_type == "IMAGE":
            if len(parts) >= 4:
                author = parts[1]
                filename = parts[2]
                b64_img = parts[3]
                try:
                    img_data = base64.b64decode(b64_img)
                    pil_img = Image.open(io.BytesIO(img_data))
                    ctk_img = CTkImage(pil_img, size=(300, 300))
                    self.add_message(f"{author} надіслав(ла) зображення: {filename}", img=ctk_img)
                except Exception as e:
                    self.add_message(f"Помилка відображення зображення: {e}")

        else:
            self.add_message(line)

    def open_image(self):
        file_name = filedialog.askopenfilename()
        if not file_name:
            return
        try:
            with open(file_name, "rb") as f:
                raw = f.read()
            b64_data = base64.b64encode(raw).decode()
            short_name = os.path.basename(file_name)
            data = f"IMAGE@{self.username}@{short_name}@{b64_data}\n"
            self.sock.sendall(data.encode())
            self.add_message('', CTkImage(light_image=Image.open(file_name), size=(300, 300)))
        except Exception as e:
            self.add_message(f"Не вдалося надіслати зображення: {e}")



    # --- АДАПТИВНЕ КОМПОНУВАННЯ ---
    def adaptive_ui(self):
        self.menu_frame.configure(height=self.winfo_height())
        self.chat_field.place(x=self.menu_frame.winfo_width(), y=0)
        self.chat_field.configure(
            width=self.winfo_width() - self.menu_frame.winfo_width() - 20,
            height=self.winfo_height() - 40
        )

        self.send_btn.place(x=self.winfo_width() - 50, y=self.winfo_height() - 40)
        self.message_entry.place(x=self.menu_frame.winfo_width(), y=self.send_btn.winfo_y())
        self.message_entry.configure(
            width=self.winfo_width() - self.menu_frame.winfo_width() - self.send_btn.winfo_width())
        self.open_img_button.place(x=self.winfo_width() - 105, y=self.send_btn.winfo_y())

        # Висота меню завжди дорівнює висоті вікна

        self.after(50, self.adaptive_ui)


# --- ЗАПУСК ---

MainWindow().mainloop()