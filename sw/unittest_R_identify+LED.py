from machine import Pin
from R_pickup_N_measure import R_measure
from locations import Resistor_Color
from R_pickup_N_measure import voltage
# Run the resistor measurement
resistor_color = R_measure()
# Map the value back to the class attribute name
color_names = {
    Resistor_Color.red: "red",
    Resistor_Color.yellow: "yellow",
    Resistor_Color.green: "green",
    Resistor_Color.blue: "blue",
    Resistor_Color.none: "none"
}

print(f"Resistor Color: {color_names.get(resistor_color, 'unknown')}")



