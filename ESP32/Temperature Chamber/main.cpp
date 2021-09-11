#include <math.h>
#include <tuple>

#include "arduino.h"
#include "driver/ledc.h"
#include "Wire.h"
#include "TMP117.h"


// Settings  

constexpr int average = 64;

double Kp = 1;
double Ki = 0.005;
double Kd = 0.0; 

// Temperature (C) and dwell time (s)
constexpr double waveform[][2] =
{
    {20, 1800},
    {15, 1800},
    {20, 1800},
    {25, 1800},
    {30, 1800},
    {25, 1800}
};


// Global variables

TMP117 sensor(0x4A);

bool newTemperature = false;
double temperature = 0;


// Functions

double getSetpoint(double t)
{
    static double t_ = double(millis()) / 1000.;
    static size_t index = 0;

    while (true)
        if (t_ + waveform[index][1] < t)
        {
            t_ += waveform[index][1];
            index++;

            if (index >= sizeof(waveform) / sizeof(waveform[0]))
                index = 0;
        }
        else
            break;

    return waveform[index][0];
}

std::tuple<double, double, double, double> pid(double t, double T, double sp, double Kp, double Ki, double Kd)
{
    static double t_ = 0;
    static double T_ = 0;
    static double e_ = 0;
    static double integral = 0;
    static bool init = false;

    double p = 0;
    double i = 0;
    double d = 0;
    double output = 0;

    double e = sp - T;
    double dt = t - t_;

    if (init)
    {
        if (abs(e) > 1.)
            integral = 0;
        else
            integral += e * dt;

        double dedt = (e - e_) / dt;

        p = e * Kp;
        i = integral * Ki;
        d = dedt * Kd;

        output = p + i + d;
    }
    else
        init = true;

    t_ = t;
    T_ = T;
    e_ = e;

    return std::make_tuple(output, p, i, d);
}

void getTemperature() 
{
    static int count = 0;
    static double sum = 0.;

    count++;
    sum += sensor.getTemperature();

    if (count == average)
    {
        newTemperature = true;
        temperature = sum / average;
        count = 0;
        sum = 0;
    }
}

void peltier(double x)
{
    x = (x >  1) ? +1. : x;
    x = (x < -1) ? -1. : x;

    int out = static_cast<int>(round(x * 255));

    if (out < 0)
    {
        dacWrite(25, -out);
        dacWrite(26, 0);
    }
    else
    {
        dacWrite(25, 0);
        dacWrite(26, out);
    }
}


// Code

void setup()
{
    pinMode(33, OUTPUT);     // TMP116 power pin
    digitalWrite(33, HIGH);  // Power up TMP116
 
    Wire.begin(21, 19);
    Serial.begin(115200);

    sensor.init(getTemperature);
    sensor.setConvMode(CONTINUOUS);

    sensor.setConvTime(C15mS5);
    sensor.setAveraging(NOAVE);
}

void loop() 
{
    double t = double(millis()) / 1000.;
    
    if (newTemperature)
    {
        newTemperature = false;
        double sp = getSetpoint(t);
        
        auto data = pid(t, temperature, sp, Kp, Ki, Kd);
        
        Serial.print("t: ");
        Serial.print(t);
        Serial.print(", T: ");
        Serial.print(temperature, 3);
        Serial.print(", SP: ");
        Serial.print(sp, 3);
        Serial.print(", Out: ");
        Serial.print(std::get<0>(data), 3);
        Serial.print(", P: ");
        Serial.print(std::get<1>(data), 3);
        Serial.print(", I: ");
        Serial.print(std::get<2>(data), 3);
        Serial.print(", D: ");
        Serial.println(std::get<3>(data), 3);

        peltier(std::get<0>(data));
        //peltier(0);
    }

    sensor.update();
    delay(1);
}
