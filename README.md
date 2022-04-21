<p align="center">
    <img src="redfox.png" alt="react beautiful dnd logo" />
</p>
<h1 align="center">RedWolf</h1>

---

<div align="center">

A proof-of-concept algorithmic trading framework optimised in high-frequency and arbitrage trading

</div>

## Implemented Brokers
- Binance

## Usage
To run RedWolf, first clone the repository.
```bash
git clone https://github.com/justusip/redwolf.git
cd redwolf
```
Prepare a .env file containing your Binance API key and secret placed at the project root.
```
BINANCE_API_KEY=...
BINANCE_SECRET=...
```
Start the service via the following command.
```bash
python3 main.py
```
```
[+][22/04 00:07:25.061783][Core] Initializing...
[+][22/04 00:07:25.068504][ UI ] Started interfacing server on localhost:2255
[#][22/04 00:07:25.105159][BNRS] [->][GET] /api/v3/time {}
[#][22/04 00:07:25.251526][BNRS] [<-][200] {'serverTime': 1650557245220}
[+][22/04 00:07:25.251770][BNXX] Google NTP time:     1650557245099 (11ms behind).
[+][22/04 00:07:25.251927][BNXX] Binance server time: 1650557245220 (115ms behind).
[#][22/04 00:07:25.252059][BNRS] [->][GET] /api/v3/exchangeInfo {}
[#][22/04 00:07:25.486054][BNRS] [<-][200] (hidden - 2745942 bytes)
[#][22/04 00:07:25.517089][BNRS] [->][GET] /sapi/v1/asset/tradeFee {'timestamp': 1650557245516, 'signature': 'e9e11a38602766c74d9aac8f53b67850faa4da053ae49cd299871b3855564107'}
[#][22/04 00:07:25.650099][BNRS] [<-][200] (hidden - 157181 bytes)
[#][22/04 00:07:25.653106][BNRS] [->][GET] /api/v3/ticker/bookTicker {}
[#][22/04 00:07:25.748239][BNRS] [<-][200] (hidden - 253997 bytes)
[#][22/04 00:07:25.752183][BNRS] [->][GET] /api/v3/ticker/24hr {}
[#][22/04 00:07:25.915073][BNRS] [<-][200] (hidden - 1109324 bytes)
[+][22/04 00:07:25.921117][BNXX] Market definitions updated. 1449 active tickers were loaded.
[+][22/04 00:07:25.921438][Core] 1 market(s) ready.
[+][22/04 00:07:25.921492][Core] Initialized. (860ms)
[+][22/04 00:07:25.921539][Core] 1 program(s) loaded.
[+][22/04 00:07:25.921748][Core] 1 program(s) up and running.
[+][22/04 00:07:25.921982][BNXX] Connecting to Binance's WebSocket market streams...
[+][22/04 00:07:26.627556][BNXX] Connected to Binance's WebSocket market streams.
```

## Implementing a Custom Trading Strategy
Please refer to the files under the programs folder.