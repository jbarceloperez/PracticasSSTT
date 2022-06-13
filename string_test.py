
def main():
    string = "GET / HTTP/1.1\nHost: 192.168.56.101:9000\nConnection: keep-alive\nCache-Control: max-age=0\nUpgrade-Insecure-Requests: 1\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36 OPR/87.0.4390.45\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9\nAccept-Encoding: gzip, deflate\nAccept-Language: es-ES,es;q=0.9"
    print(string + "\n\n")
    print(string.splitlines())
    print("\n\n")
    print(string.split())


if __name__=="__main__":
    main()