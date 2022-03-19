
#include <Wire.h>

#define UNO_ADDR 9
#define BLK_SIZE 16
#define MAX_DATA_LENGTH 511

String msg = "Arduino rcvd: ";
String sendMsg = "";

bool inRcv = false;
int  rcvLen = 0;
int  rcvBlk = 0;

bool inSend = false;
int  sendLen = 0;
int  sendOffset = 0;
int  sendBlkCnt = 0;

int  dataOffset = 0;
char data[MAX_DATA_LENGTH+1]; 

bool ledState = LOW;  // toggle ledState as we read

union ArrayToInteger {
  byte array[4];
  uint32_t integer;
};

void setup()
{
  Serial.begin(9600);
  pinMode(LED_BUILTIN, OUTPUT);
  Wire.begin(UNO_ADDR);
  /*Event Handlers*/
  Wire.onReceive(DataReceive);
  Wire.onRequest(DataRequest);
}

void loop()
{
  delay(50);
}

void toggleLedState()
{
  ledState = !ledState;
  digitalWrite(LED_BUILTIN, ledState);
  
}
void DataReceive(int numBytes)
{ 
  if (!inRcv)
  {
    // should receive 4 bytes 
    // with length of remainder of message
    ArrayToInteger converter; //Create a converter
    int i=0;
    while(Wire.available() && i < 4) 
    { 
      converter.array[i++] = Wire.read();
    }

    // require minimum 4 bytes to start a message
    // if not received, ignore the request
    if (i < 4)
    {
      Serial.print("ignoring Wire.onRequest(), msg len = ");
      Serial.println(i);
      Serial.println("***********");
      return;
    }

    rcvLen = converter.integer;

    Serial.print("Message length: ");
    Serial.print(rcvLen);

    inRcv = true;
    rcvBlk = 1;
    dataOffset = 0;
    memset(data,0, rcvLen+1);
  }
  else {
    rcvBlk++;
  }

  toggleLedState();
  while(Wire.available() && dataOffset < rcvLen) 
  { 
    // ignore any data beyond the max buffer size
    if (dataOffset > MAX_DATA_LENGTH){
      Wire.read();
      dataOffset++;
    }
    else {
      data[dataOffset++] = Wire.read();
    }
  }

  if (dataOffset >= rcvLen)
  {
    Serial.print(" block count: ");
    Serial.println(rcvBlk);

    if (rcvLen > MAX_DATA_LENGTH)
    {
      Serial.println("*** WARNING *** ignored data beyond buffer size");
    }

    Serial.print("rcvd: ");
    Serial.println(data);
    Serial.println("***********");
    
    inRcv = false;
    digitalWrite(LED_BUILTIN, LOW);
  }

}


// Data requested by controller
void DataRequest()
{
  if (!inSend)
  {
    inSend = true;
    sendLen = msg.length();
    sendMsg = msg;
    if (rcvLen > 0)
    {
      // Serial.println("*** adding received data to send data");
      sendMsg = sendMsg + String(data);
      sendLen = sendMsg.length();
    }
    sendOffset = 0;
    sendBlkCnt = 1;

    // send message length
    ArrayToInteger converter; //Create a converter
    converter.integer = sendLen;
    Wire.write(converter.array, 4);
  }
  else 
  {
    toggleLedState();
    ++sendBlkCnt;
    
    int bufferLen = BLK_SIZE;
    if (sendLen < BLK_SIZE)
    {
      bufferLen = sendLen;
    }

    byte resp[bufferLen];
    for (byte i=0; i<bufferLen; ++i) {
      resp[i] = (byte)sendMsg.charAt(sendOffset++);
      --sendLen;
    }
    Wire.write(resp, bufferLen);

    if (sendLen <= 0)
    {
      Serial.print("Sent resp ");
      Serial.print(sendMsg.length());
      Serial.print(" bytes long in ");
      Serial.print(sendBlkCnt);
      Serial.println(" blocks");
      Serial.print("sent: ");
      Serial.println(sendMsg);
      Serial.println("***********");
      inSend = false;
      sendLen = 0;
      sendOffset = 0;
      digitalWrite(LED_BUILTIN, LOW);
    }
  }
}
