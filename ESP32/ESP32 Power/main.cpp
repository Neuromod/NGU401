#include "arduino.h"
#include "esp_sleep.h"
#include "WiFi.h"

#include "Secret.h"


enum class State
{
    Idle,
    Computation,
    WifiConnect,
    WifiIdle,
    WifiDownload,
    WifiUpload,
    WifiDisconnect,
    LightSleep,
    LightSleepDelay,
    DeepSleep,
    DeepSleepDelay,
    Reset,
};


constexpr uint8_t       ledPin        = 2;
constexpr uint8_t       triggerPin    = 21;
constexpr uint32_t      delayDuration = 3000;
constexpr unsigned long dataTransfer  = 1000000;
constexpr unsigned      blinkDuration = 50;

RTC_DATA_ATTR State state = State::Idle;

auto signal(unsigned duration) -> void
{
    digitalWrite(triggerPin, 1);
    delay(duration);
    digitalWrite(triggerPin, 0);
}


auto setup() -> void
{
    Serial.begin(115200);

    while (true)
    {
        pinMode(triggerPin, OUTPUT);
        signal(blinkDuration);

        switch (state)
        {
        case State::Idle:
            {
                Serial.print("Idle...\n");
                state = State::Computation;

                delay(delayDuration);
                
                break;
            }

        case State::Computation:
            {
                Serial.print("Computation...\n");
                state = State::WifiConnect;
                
                volatile int i0 = 1234567890;
                volatile int i1 = 12345;
                volatile int iv = 0;

                volatile float f0 = 1. / 3.;
                volatile float f1 = 2. / 3.;
                volatile float fv = 0.;

                volatile double d0 = 1. / 3.;
                volatile double d1 = 2. / 3.;
                volatile double dv = 0.;

                auto t0 = millis();

                while (true)
                {
                    for (int i = 0; i < 50; i++)
                        iv += i0;
                        iv /= i1;
                        iv -= i1;
                        iv *= i0;
                        
                        fv += f0;
                        fv /= f1;
                        fv -= f1;
                        fv *= f0;
                        fv = std::pow(fv, 1. / 3.);
                        fv += std::sin(fv);
                        
                        dv += d0;
                        dv /= d1;
                        dv -= d1;
                        dv *= d0;
                        dv = std::pow(dv, 1. / 3.);
                        dv += std::sin(dv);

                    if (millis() - t0 > delayDuration)
                        break;
                }
            
                break;
            }

        case State::WifiConnect:
            {
                Serial.print("WiFi connection...\n");
                state = State::WifiIdle;

                unsigned long t = millis();

                wl_status_t status = WiFi.begin(ssid, pass);

                while (true)
                {
                    if (status == WL_CONNECTED)
                        break;

                    status = WiFi.status();
                }

                break;
            }

        case State::WifiIdle:
            {
                Serial.print("WiFi idling...\n");
                state = State::WifiDownload;

                delay(delayDuration);

                break;
            }

        case State::WifiDownload:
            {
                Serial.print("WiFi download... ");
                state = State::WifiUpload;

                unsigned long transferred = 0;

                WiFiClient client;
                client.connect(downloadServer, downloadPort);
                
                unsigned long t0 = millis();

                while (transferred < dataTransfer)
                    if (client.read() != -1)
                        transferred++;

                unsigned long t1 = millis();

                Serial.print(static_cast<double>(dataTransfer) / static_cast<double>(t1 - t0));
                Serial.print(" kB/s\n");
                
                client.stop();
                
                break;
            }

        case State::WifiUpload:
            {
                Serial.print("WiFi upload... ");
                state = State::WifiDisconnect;

                WiFiClient client;
                client.connect(uploadServer, uploadPort);

                unsigned long t0 = millis();

                char block[1400];

                for (int i = 0; i < sizeof(block) - 1; i++)
                    block[i] = static_cast<char>(static_cast<int>('a') + i % 26);

                for (unsigned long transferred = 0; transferred < dataTransfer / sizeof(block); transferred++)
                    client.write(block, sizeof(block));

                unsigned long remainder = dataTransfer % sizeof(block);

                if (remainder)
                    client.write(block, remainder);

                unsigned long t1 = millis();

                Serial.print(static_cast<double>(dataTransfer) / static_cast<double>(t1 - t0));
                Serial.print(" kB/s\n");
                
                client.stop();

                break;
            }

        case State::WifiDisconnect:
            {
                Serial.print("WiFi disconnect...\n");
                state = State::LightSleep;

                WiFi.disconnect();

                break;
            }

        case State::LightSleep:
            {
                Serial.print("Light Sleep (no delay)...\n");
                Serial.flush();
                state = State::LightSleepDelay;
                
                esp_sleep_enable_timer_wakeup(0);
                esp_light_sleep_start();
                
                break;
            }

        case State::LightSleepDelay:
            {
                Serial.print("Light Sleep (delayed)...\n");
                Serial.flush();                
                state = State::DeepSleep;    

                esp_sleep_enable_timer_wakeup(1000 * delayDuration);
                esp_light_sleep_start();
                
                break;
            }

        // Reset keeping only data of RTC_DATA_ATTR variables
        case State::DeepSleep:
            {
                Serial.print("Deep sleep (no delay)...\n");
                Serial.flush();
                state = State::DeepSleepDelay;

                esp_sleep_enable_timer_wakeup(0);
                esp_deep_sleep_start();
            }

        // Reset keeping only data of RTC_DATA_ATTR variables
        case State::DeepSleepDelay:
            {
                Serial.print("Deep sleep (delayed)...\n");
                Serial.flush();
                state = State::Reset;
                
                esp_sleep_enable_timer_wakeup(1000 * delayDuration);
                esp_deep_sleep_start();
            }

        // Full reset
        case State::Reset:
            {
                Serial.print("Restarting...\n");
                esp_restart();
            }
        }
    }
}

void loop() 
{
}
