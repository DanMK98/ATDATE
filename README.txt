PRÁCTICA: PROTOCOLO TIME

Nombre y apellidos: Daniel Mihailov Kostov
Correo electrónico: 100550843@alumnos.uc3m.es

Comentarios sobre atdate.py:

- Implementado en Python 3, utilizando únicamente la biblioteca estándar.
  Ejecución: python3 atdate.py [opciones].
- Las comunicaciones utilizan IPv4.
- El cliente UDP tiene un tiempo de espera de 5 segundos. El cliente TCP
  aplica ese límite a la conexión inicial y después espera las actualizaciones
  sin límite de tiempo, hasta la desconexión o la interrupción del usuario.
- El cliente TCP acumula los datos recibidos hasta completar los 4 bytes
  del timestamp, aunque lleguen en varias lecturas.

Diferencias respecto al enunciado que deben tenerse en cuenta:

- Si se omite -s en modo consulta, se utiliza localhost en lugar de rechazar
  la ejecución por falta del argumento obligatorio.
- La fecha se muestra en hora local con el formato
  "Current time: AAAA-MM-DD HH:MM:SS", sin abreviatura de zona horaria,
  en lugar del formato indicado en los ejemplos del enunciado.
- Si el servidor TCP cierra la conexión, el cliente lo comunica como error
  de conexión, incluso cuando el último timestamp se recibió completo.
  