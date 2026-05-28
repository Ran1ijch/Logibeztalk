import threading
from socket import *
from customtkinter import *


class MainWindow(CTk):
   def __init__(self):
       super().__init__()
       self.geometry('400x300')
       self.title("Чат")
       
       self.label = None
       self.entry = None
       self.menu_width = 30
       
       # 1. ГОЛОВНИЙ КОНТЕЙНЕР
       self.main_container = CTkFrame(self, fg_color="transparent")
       self.main_container.pack(side=RIGHT, fill=BOTH, expand=True, padx=5, pady=5)
       
       # Поле чату
       self.chat_field = CTkTextbox(self.main_container, font=('Arial', 14, 'bold'), state='disabled')
       self.chat_field.pack(side=TOP, fill=BOTH, expand=True, pady=(0, 5))
       
       # Нижня панель
       self.bottom_frame = CTkFrame(self.main_container, fg_color="transparent")
       self.bottom_frame.pack(side=BOTTOM, fill=X)
       
       # Кнопка відправки
       self.send_button = CTkButton(self.bottom_frame, text='>', width=50, height=40, command=self.send_message)
       self.send_button.pack(side=RIGHT, padx=(5, 0))
       
       # Поле вводу
       self.message_entry = CTkEntry(self.bottom_frame, placeholder_text='Введіть повідомлення:', height=40)
       self.message_entry.pack(side=LEFT, fill=X, expand=True)

       # 2. БІЧНЕ МЕНЮ
       self.menu_frame = CTkFrame(self, width=self.menu_width)
       self.menu_frame.pack_propagate(False) 
       self.menu_frame.pack(side=LEFT, fill=Y)
       
       self.is_show_menu = False
       
       # Кнопка тригера меню
       self.btn = CTkButton(self, text='▶️', command=self.toggle_show_menu, width=30)
       self.btn.place(x=0, y=0)

       # Мережева логіка
       self.username = 'Rani'
       try:
           self.sock = socket(AF_INET, SOCK_STREAM)
           self.sock.connect(('2.tcp.eu.ngrok.io', 16172))
           hello = f"TEXT@{self.username}@[SYSTEM] {self.username} приєднався(лась) до чату!\n"
           self.sock.send(hello.encode('utf-8'))
           
           # Запуск фонового потоку
           threading.Thread(target=self.recv_message, daemon=True).start()
       except Exception as e:
           self.safe_add_message(f"[Система]: Не вдалося підключитися: {e}")

   def toggle_show_menu(self):
       if self.is_show_menu:
           self.is_show_menu = False
           self.btn.configure(text='▶️')
           if self.label and self.entry:
               self.label.destroy()
               self.entry.destroy()
               self.label = None
               self.entry = None
           self.show_menu()
       else:
           self.is_show_menu = True
           self.btn.configure(text='◀️')
           self.show_menu()

   def show_menu(self):
       if self.is_show_menu and self.menu_width < 200:
           self.menu_width += 15
           if self.menu_width > 200: self.menu_width = 200
           self.menu_frame.configure(width=self.menu_width)
           self.after(10, self.show_menu)
           
           if self.menu_width == 200 and not self.label:
               self.label = CTkLabel(self.menu_frame, text='Імʼя')
               self.label.pack(pady=30)
               self.entry = CTkEntry(self.menu_frame)
               self.entry.pack()
               
       elif not self.is_show_menu and self.menu_width > 30:
           self.menu_width -= 15
           if self.menu_width < 30: self.menu_width = 30
           self.menu_frame.configure(width=self.menu_width)
           self.after(10, self.show_menu)

   def safe_add_message(self, text):
       self.after(0, self._add_message_ui, text)

   def _add_message_ui(self, text):
       self.chat_field.configure(state='normal')
       self.chat_field.insert(END, text + '\n')
       self.chat_field.configure(state='disabled')
       self.chat_field.see(END)

   def send_message(self):
       message = self.message_entry.get()
       if message:
           # Відображаємо у себе локально
           self.safe_add_message(f"Я: {message}")
           
           data = f"TEXT@{self.username}@{message}\n"
           try:
               self.sock.sendall(data.encode('utf-8'))
           except Exception as e:
               self.safe_add_message(f"[Система]: Помилка відправки: {e}")
       self.message_entry.delete(0, END)

   def recv_message(self):
       buffer = ""
       while True:
           try:
               chunk = self.sock.recv(4096)
               if not chunk:
                   self.safe_add_message("[Система]: Сервер розірвав з'єднання.")
                   break
               
               buffer += chunk.decode('utf-8', errors='ignore')

               while "\n" in buffer:
                   line, buffer = buffer.split("\n", 1)
                   self.handle_line(line.strip())
           except Exception as e:
               # Якщо виникне будь-яка помилка сокета — ми її побачимо в чаті
               self.safe_add_message(f"[Система]: Помилка потоку читання: {e}")
               break
       self.sock.close()

   def handle_line(self, line):
       if not line:
           return

       # Розбиваємо рядок по символу '@'
       parts = line.split("@")
       msg_type = parts[0]

       if msg_type == "TEXT":
           if len(parts) >= 3:
               author = parts[1]
               # Збираємо текст назад (якщо в повідомленні теж були символи '@')
               message = "@".join(parts[2:]) 
               
               # Якщо це повідомлення від іншого користувача — показуємо його
               if author != self.username:
                   self.safe_add_message(f"{author}: {message}")
           else:
               # Якщо сервер прислав TEXT, але частин менше ніж 3
               self.safe_add_message(f"[Система/Сирий TEXT]: {line}")
               
       elif msg_type == "IMAGE":
           if len(parts) >= 3:
               author = parts[1]
               filename = parts[2]
               if author != self.username:
                   self.safe_add_message(f"{author} надіслав(ла) зображення: {filename}")
       else:
           # УЛОВЛЮВАЧ ВСЬОГО: якщо сервер прислав повідомлення в будь-якому іншому форматі,
           # ми не ігноруємо його, а просто виводимо на екран як є.
           self.safe_add_message(line)


if __name__ == "__main__":
    win = MainWindow()
    win.mainloop()