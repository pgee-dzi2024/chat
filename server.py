# Импортираме нужните модули: socket за мрежова комуникация и threading за нишки
import socket
import threading

# Адрес и порт, на които сървърът ще слуша (127.0.0.1 = локална машина)
HOST = '127.0.0.1'
PORT = 5000

# Множество (set) от активни клиентски сокети, към които ще изпращаме съобщения
clients = set()
# Заключване (Lock) за безопасен едновременен достъп до множеството clients от много нишки
clients_lock = threading.Lock()

# Функция за разпращане (broadcast) на съобщение до всички клиенти (без източника)
def broadcast(message: bytes, source_sock=None):
    # Вземаме заключването, за да работим безопасно с общото множество clients
    with clients_lock:
        # Списък с "изпаднали" клиенти, към които не е било успешно изпращането
        dead = []
        # Обхождаме всички клиентски сокети
        for c in clients:
            # Прескачаме източника (ако не искаме той да получава собственото си съобщение)
            if c is source_sock:
                continue
            try:
                # Изпращаме съобщението като байтов низ (bytes)
                c.sendall(message)
            except Exception:
                # Ако има грешка при изпращане, отбелязваме този сокет за почистване
                dead.append(c)
        # Премахваме "мъртвите" връзки от множеството и ги затваряме
        for d in dead:
            clients.remove(d)
            d.close()

# Функция за обработка на отделен клиент; стартира се в отделна нишка
def handle_client(conn: socket.socket, addr):
    try:
        # Пращаме първоначално съобщение: молим клиента да въведе име
        conn.sendall(b'Welcome! Type your name: ')
        # Четем до 1024 байта от клиента (първия ред), декодираме от UTF-8 и махаме крайни интервали
        name = conn.recv(1024).decode('utf-8', errors='ignore').strip()
        # Ако не е подадено име, правим резервно име по IP:порт
        if not name:
            name = f'{addr[0]}:{addr[1]}'

        # Съставяме съобщение за присъединяване и го показваме на конзолата на сървъра
        join_msg = f'>> {name} joined the chat\n'.encode('utf-8')
        print(join_msg.decode('utf-8').strip())
        # Разпращаме съобщението за присъединяване до всички клиенти
        broadcast(join_msg, source_sock=None)

        # Добавяме текущия клиент към множеството активни клиенти (с заключване)
        with clients_lock:
            clients.add(conn)

        # Инструкции към клиента как да напусне чата
        conn.sendall(b'You can start typing messages. Type /quit to exit.\n')

        # Главен цикъл за четене на съобщения от този клиент
        while True:
            # Четем до 1024 байта; ако връзката е затворена, recv връща b'' (празно)
            data = conn.recv(1024)
            # Ако няма данни, клиентът е прекъснал връзката — излизаме от цикъла
            if not data:
                break
            # Декодираме съобщението от UTF-8 и премахваме крайни интервали/нови редове
            text = data.decode('utf-8', errors='ignore').strip()
            # Ако клиентът е написал командата /quit — прекратяваме цикъла (напуска чата)
            if text == '/quit':
                break
            # Форматираме съобщението в стил: [име] текст
            msg = f'[{name}] {text}\n'.encode('utf-8')
            # Разпращаме съобщението до всички останали клиенти (изключваме източника)
            broadcast(msg, source_sock=conn)
    except Exception as e:
        # Ако възникне грешка по време на работа с този клиент, логваме я
        print(f'Error with {addr}: {e}')
    finally:
        # Винаги, при излизане (нормално или при грешка), почистваме клиента
        with clients_lock:
            if conn in clients:
                clients.remove(conn)
        # Затваряме сокета на клиента
        conn.close()
        # Изпращаме съобщение към всички, че клиентът е напуснал
        leave_msg = f'<< {addr[0]}:{addr[1]} left the chat\n'.encode('utf-8')
        broadcast(leave_msg)
        # Печатаме и в конзолата на сървъра
        print(leave_msg.decode('utf-8').strip())

# Главна функция, която подготвя сървъра и приема нови връзки
def main():
    # Създаваме TCP сокет (AF_INET за IPv4, SOCK_STREAM за TCP)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Разрешаваме повторно използване на адрес при бързо рестартиране (полезно в разработка)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Закачаме сокета към дадения адрес и порт
        s.bind((HOST, PORT))
        # Слушаме за входящи връзки (по подразбиране backlog е достатъчен)
        s.listen()
        # Информативно съобщение, че сървърът е стартирал
        print(f'Server listening on {HOST}:{PORT}')

        # Безкраен цикъл за приемане на нови клиенти
        while True:
            # Приемаме входяща връзка; връща нов сокет (conn) и адрес на клиента (addr)
            conn, addr = s.accept()
            # Показваме в конзолата, че има нова връзка
            print(f'Connection from {addr}')
            # За всеки клиент стартираме отделна нишка, която ще изпълнява handle_client
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            # Стартираме нишката
            t.start()

# Точка на вход: ако файлът се пуска директно, извикваме main()
if __name__ == '__main__':
    main()