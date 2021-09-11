#include <math.h>

#include "arduino.h"
#include "driver/ledc.h"
#include "Wire.h"
#include "TMP117.h"


TMP117 sensor(0x4A);

void newTemperature() 
{
    Serial.println(sensor.getTemperature(), 4);
}

void setup()
{
    pinMode(33, OUTPUT);     // TMP116 power pin
    digitalWrite(33, HIGH);  // Power up TMP116

    Wire.begin(21, 19);
    Serial.begin(115200);

    sensor.init (newTemperature);
    sensor.setConvMode(CONTINUOUS);

    sensor.setConvTime(C15mS5);
    sensor.setAveraging(NOAVE);
}

void loop() 
{
    sensor.update();
    delay(1);
}
