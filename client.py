# Импортираме socket за мрежова комуникация, threading за нишка за приемане и sys за четене от конзолата
import socket
import threading
import sys

# Адрес и порт на сървъра — трябва да съвпадат с тези от server.py
HOST = '127.0.0.1'
PORT = 5000

# Функция, която ще върви в отделна нишка и ще получава (принтира) всички входящи съобщения от сървъра
def recv_loop(sock: socket.socket):
    try:
        # Безкраен цикъл за приемане на данни
        while True:
            # Четем до 1024 байта от сървъра
            data = sock.recv(1024)
            # Ако сървърът е затворил връзката, recv връща b'' (празно)
            if not data:
                print('Server closed the connection.')
                break
            # Декодираме от UTF-8 и печатаме без да добавяме втори нов ред (затова end='')
            print(data.decode('utf-8'), end='')
    except Exception as e:
        # Ако има грешка при приемане, я показваме
        print(f'Receive error: {e}')
    finally:
        # При излизане от цикъла се опитваме учтиво да затворим връзката
        try:
            # Забраняваме по-нататъшно изпращане/получаване
            sock.shutdown(socket.SHUT_RDWR)
        except:
            # Игнорираме грешки при shutdown (например ако вече е затворен)
            pass
        # Затваряме сокета окончателно
        sock.close()

# Главна функция на клиента
def main():
    # Създаваме TCP сокет
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Свързваме се към сървъра на зададения адрес и порт
        s.connect((HOST, PORT))

        # Стартираме отделна нишка, която ще слуша входящите съобщения и ще ги печата
        t = threading.Thread(target=recv_loop, args=(s,), daemon=True)
        # Стартираме нишката за приемане
        t.start()

        try:
            # Четем ред по ред от стандартния вход (конзолата)
            for line in sys.stdin:
                # Изпращаме реда към сървъра (кодиране в UTF-8)
                s.sendall(line.encode('utf-8'))
                # Ако въведем командата /quit, прекратяваме цикъла (искаме да затворим)
                if line.strip() == '/quit':
                    break
        except KeyboardInterrupt:
            # Ако потребителят натисне Ctrl+C, просто излизаме чисто
            pass
        finally:
            # Опитваме да спрем комуникацията учтиво
            try:
                s.shutdown(socket.SHUT_RDWR)
            except:
                pass
            # Контекстният мениджър (with ...) ще затвори сокета автоматично тук

# Точка на вход: ако файлът се пуска директно, извикваме main()
if __name__ == '__main__':
    main()