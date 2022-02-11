# ws-proxy

This is a small FastAPI application that serves as web-socket proxy.

Every message received is passed through to the same channel.

### Channels

The channels are split by application and channel id so several applications can use the same server as web socket proxy

Typical address is:
```
ws://{server}/ws/channel/{application_name}/{channel_id}
```

### Testing

```
pytest --cov=app --cov-report=html --cov-fail-under 100
```