# pyWSDscan

Cross-platform open-source Python tool to interact with a network scanner using the Microsoft WSD (Web Services on Devices) WS-Scan protocol.

Tested on a Fuji Xerox DocuPrint CM115w.

## Example usage

Replace `http://192.168.0.2:9867/ws2/` with the applicable URL for your network scanner.

Basic usage:

    ./main.py http://192.168.0.2:9867/ws2/ scan > out.jpg

This will scan a document using the scanner's default settings.

Specifying more options:

    ./main.py http://192.168.0.2:9867/ws2/ scan --quality 95 --type Text --format exif --size a4 --source ADFDuplex --color BlackAndWhite1 --ppi 300 --region '10x20+3,4 cm' > out.jpg

This will scan an A4 document from the duplex-capable Automatic Document Feeder using the text profile, at 300 pixels per inch. The region scanned is a 10 cm by 20 cm region, which is offset by 3 cm along the x-axis and 4 cm along the y-axis. The image will be scanned as 1 bit-per-pixel black and white, and stored as an Exif (JPEG) image at 95% quality.

Specifying separate options for front and back pages (ADFDuplex only):

    ./main.py http://192.168.0.2:9867/ws2/ scan --source ADFDuplex --color RGB24 BlackAndWhite1 --ppi 600 300 --region Default '10x20+3,4 cm' > out.jpg

The front will be 24 bit-per-pixel RGB colour on the front side, at 600 pixels per inch, using the whole scan area. The back will be 1 bit-per-pixel black and white, at 300 pixels per inch, using the 10x20 cm region from earlier.
