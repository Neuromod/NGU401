#include "WiFi.h"

constexpr char ssid[] = "SSID";
constexpr char pass[] = "PASSWORD";

const IPAddress downloadServer(192, 168, 0, 10);
const IPAddress uploadServer(192, 168, 0, 10);

const unsigned int downloadPort = 19;
const unsigned int uploadPort = 9;