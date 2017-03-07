#include <dht.h>

/* Defines */
// Number of sensors
#define temp_s 5
#define humid_s 1
#define press_s 0

// The DHT11 input pin on the arduino board
#define DHT11_PIN 4

// The delay time between transmissions to the RasPi
//#define milliseconds 60000
#define milliseconds 1000

/* Declarations */

// Each LM35 sensor has a slighty different multiplier
// The multipliers convers the Voltage reading to Celsius degrees
// 1/9.31   1/9.31   1/9.31   1/9.31   
float multipliers[5] = { 0.107411, 0.107411, 0.107411, 0.107411, 0.107411 };
float offsets[5] = { 0, 0, 0, 0, 0 };

// Loopstate will tell the loop function what it should do
// whether it is to get another reading for the AVG or to
// calc the average and output the result
// 0->MAX-1: NUMBERS WILL BE ADDED FOR  THE AVG
// MAX: AVG WILL BE CALCULATED AND PRINTED
#define LOOPSTATE_MAX 300
int cur_loop = 0;

// The temperature arrays
float temps_raw[temp_s][LOOPSTATE_MAX];
float temps_avg[temp_s];
// The humidity arrays
float humid_raw[humid_s][LOOPSTATE_MAX];
float humid_avg[humid_s];
// A DHT object. It will be storing the sensor readings
dht DHT1;

// About the output
// Currently #3 #4 on A1 A2
int lm_outs[temp_s] = { 0, 1, 2, 3, 4 };


// This function is called once in the start
void setup() {
  
  // Configures the reference voltage used for analog input, equal to 1.1 V
  // Arduino UNO -> INTERNAL
  // Arduino MEGA -> INTERNAL1V1
  analogReference(INTERNAL1V1);

  // Sets the data rate in bits per second (baud) for serial data transmission
  Serial.begin(9600);
  
}

// This function loops forever
void loop() {

  // Check for the current loop and do things
  // If current loop has not yet reached max, update the avg readings
  // If current loop has reached max, calculate the averages for every LM
  // get the humidity and print the results
  if (cur_loop < LOOPSTATE_MAX) {
    
    // Read the temperatures
    for(int num=0; num<temp_s; num++) {
      temps_raw[num][cur_loop] = analogRead(lm_outs[num]) * multipliers[lm_outs[num]] + offsets[lm_outs[num]];
    }

    // Read the huidities
    for(int num=0; num<humid_s; num++) {
      //DHT1.read11(DHT11_PIN);
      //humid_raw[num][cur_loop] = DHT1.humidity;
      humid_raw[num][cur_loop] = 0.0;
    }
    
  }
  else if (cur_loop == LOOPSTATE_MAX) {

    // Calculate the temperature averages
    for(int num=0; num<temp_s; num++) {
      float sum = 0;
      for(int inloop=0; inloop<LOOPSTATE_MAX; inloop++) {
        sum += temps_raw[num][inloop];
      }
      temps_avg[num] = sum / LOOPSTATE_MAX;
    }

    // Calculate the humidity averages
    for(int num=0; num<humid_s; num++) {
      float sum = 0;
      for(int inloop=0; inloop<LOOPSTATE_MAX; inloop++) {
        sum += humid_raw[num][inloop];  
      }
      humid_avg[num] = sum / LOOPSTATE_MAX;
    }

    DHT1.read11(DHT11_PIN);

    // Print the temperatures to the serial port as ASCII text
    print_output();
  }

  // Update the current loop
  cur_loop++;
  if(cur_loop > LOOPSTATE_MAX)
    cur_loop = 0;

  // Pause for some time
  delay(milliseconds / LOOPSTATE_MAX);
}

void print_output() {

  // Print the temperatures
  for(int num=0; num<temp_s; num++) {
    Serial.print(temps_avg[num]);
    Serial.print(" ");
  }

  // Print the humidities
  //for(int num=0; num<humid_s; num++) {
  //  Serial.print(humid_avg[num]);
  //  Serial.print(" ");  
  //}
  Serial.print(DHT1.humidity);
  Serial.print(" ");

  Serial.println();
  
}

