from R_pickup_N_measure import R_measure
from sw.locations import Resistor_Color

# Run the resistor measurement
resistor_color = R_measure()

#test map to map class attribute names
color_map = {
    Resistor_Color.blue: "Blue",
    Resistor_Color.green: "Green",
    Resistor_Color.red: "Red",
    Resistor_Color.yellow: "Yellow",
    Resistor_Color.none: "None"
}
# Print the numeric color code
print(f"Resistor Color: {color_map.get(resistor_color, 'Unknown')}")


