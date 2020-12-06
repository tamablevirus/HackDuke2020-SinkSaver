//
//HACKDUKE 2020
//Water Drip Arduino Device Firmware
//Jackson Meade
//12.05.2020
//PACKAGES NEEDED: SPI, Wifi101, and WifiUdp

#include <SPI.h>
#include <WiFi101.h>
#include <WiFiUdp.h>



int status = WL_IDLE_STATUS;

  //!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  //ENTER YOUR WIFI NAME AND PASSWORD HERE
  //!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 

char ssid[] = "XXXXXXXXXXXX"; //  your network SSID (name)
char pass[] = "XXXXXXXXXXXX";    // your network password (use for WPA, or use as key for WEP)
char packet[255];

int localPort = 7;
byte broadCastIp[] = { 10,5,5,9 };

byte appIP[] = { 34,203,111,198 };

  //!!!!!!!!!!!!!!!!!!!!!!!!!!!
  //ENTER YOUR MAC ADDRESS HERE
  //!!!!!!!!!!!!!!!!!!!!!!!!!!! 

byte remote_MAC_ADD[] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };
int wolPort = 9;


WiFiUDP Udp;

WiFiClient client;

const char* host = "10.5.5.9";

const int httpPort = 80;

const int streamingPort = 8554;


void setup(){  

  //Initialize serial and wait for port to open:
  Serial.begin(115200);


  // check for the presence of the wifi module:
  if (WiFi.status() == WL_NO_SHIELD) {
     Serial.println("WiFi not present");
     // don't continue:
     while (true);
  }



  // attempt to connect to Wifi network:
  while ( status != WL_CONNECTED) {
    Serial.print("Attempting to connect to SSID: ");
    Serial.println(ssid);
    // Connect to WPA/WPA2 network. Change this line if using open or WEP network:
     status = WiFi.begin(ssid, pass);

    // wait 8 seconds for connection:
    delay(8000);
  }

  Serial.println("Connected to wifi");
  printWifiStatus();


}


void loop(){
  
// WAKE UP CAMERA FROM SLEEP AND CONNECT
CameraInitiate();


// START STREAM
StartStream();

//SEND TO API

delay(1000);

// STREAM TO DRIP API
sendToAPI();



delay(5000);

}


void StartStream(){
  Serial.print("connecting to ");
  Serial.println(host);

  if (!client.connect("10.5.5.9", httpPort)) {
    Serial.println("connection failed");
    return;
  }

  //Command for starting streaming
  String StartUrl = "/gp/gpControl/execute?p1=gpStream&a1=proto_v2&c1=restart ";
  Serial.print("Requesting URL: ");
  Serial.println(StartUrl);
  client.print(String("GET ") + StartUrl + " HTTP/1.1\r\n" +
  "Host: " + host + "\r\n" +
  "Connection: close\r\n\r\n");
  Serial.println("Streaming");
}





// FUNCTION TO WAKE UP THE CAMERA

void CameraInitiate(){

  //Begin UDP communication
  Udp.begin(localPort);

  //Send the magic packet to wake up the GoPro out of sleep
  delay(2000);
  SendMagicPacket();
  delay(5000);  

  // Absolutely necessary to flush port of UDP junk for Wifi client communication
  Udp.flush();
  delay(1000);

  //Stop UDP communication
  Udp.stop();
  delay(1000);

}


// Function to create and send magic packet
// Taken and translated from here:
// https://www.logicaprogrammabile.it/wol-accendere-computer-arduino-wake-on-lan/

void SendMagicPacket(){

  //Create a 102 byte array
  byte magicPacket[102];

  // Variables for cycling through the array
  int Cycle = 0, CycleMacAdd = 0, IndexArray = 0;

  // This for loop cycles through the array
  for( Cycle = 0; Cycle < 6; Cycle++){

    // The first 6 bytes of the array are set to the value 0xFF
    magicPacket[IndexArray] = 0xFF;

    // Increment the array index
    IndexArray++;
  }

  // Now we cycle through the array to add the GoPro address
  for( Cycle = 0; Cycle < 16; Cycle++ ){
    //eseguo un Cycle per memorizzare i 6 byte del
    //mac address
    for( CycleMacAdd = 0; CycleMacAdd < 6; CycleMacAdd++){
      
      magicPacket[IndexArray] = remote_MAC_ADD[CycleMacAdd];
      
      // Increment the array index
      IndexArray++;
    }
  }

  //The magic packet is now broadcast to the GoPro IP address and port
  Udp.beginPacket(broadCastIp, wolPort);
  Udp.write(magicPacket, sizeof magicPacket);
  Udp.endPacket();

}


//Function to send camera's UDP stream to online API using HTTP
void sendToAPI() {

  int packetSize = Udp.parsePacket();
  if (packetSize) {
    Serial.print("Received Camera Data! Size: ");
    Serial.println(packetSize);
    int len = Udp.read(packet, 255);
    if (len > 0)
    {
      packet[len] = '\0';
    }
  }

  Serial.println("Packet Received, broadcasting.");

  int HTTP_PORT = 80;
  String HTTP_METHOD = "POST";
  char HOST_NAME = "sink-saver.herokuapp.com/";
  String PATH_NAME = "content";
  // String QUERY = String("?file=") + String(packet);

  if (client.connect(HOST_NAME, HTTP_PORT)) {
    Serial.println("Connected to server.");

    client.println(HTTP_METHOD + " " + PATH_NAME + " HTTP/1.1");
    client.println("Host: " + String(HOST_NAME));
    client.println("Connection: close");
    client.println(); // end HTTP request header

    // client.println(QUERY);

    while(client.connected()) {
      if(client.available()) {
        client.write(packet);
      }
    } 
    
  } else {
    Serial.println("Connection failed!");
  }

  

}



}



void printWifiStatus() {
  // print the SSID of the network you're attached to:
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());

  // print your WiFi shield's IP address:
  IPAddress ip = WiFi.localIP();
  Serial.print("IP Address: ");
  Serial.println(ip);

  // print the received signal strength:
  long rssi = WiFi.RSSI();
  Serial.print("signal strength (RSSI):");
  Serial.print(rssi);
  Serial.println(" dBm");
}
}
