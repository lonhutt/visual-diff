import pika, time

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))

channel = connection.channel()

channel.queue_declare(queue='hello')

print " [*] waiting for messages. To exit press CTRL+C"

def callback(ch, method, properties, body):
  print " [x] Received %r" % (body, )
  time.sleep(body.count('.'))
  print " [x] done."

channel.basic_consume(callback, queue='hello', no_ack=True)

channel.start_consuming()