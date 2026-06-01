# Transport Vehicle Reference

---

## Key Definitions

### Payload Capacity (t)
The maximum mass of cargo the vehicle is permitted to carry, **excluding the vehicle's own unladen weight**. Also called net load capacity or nett vehicle weight.

> Example: a truck with a payload capacity of 20 t can transport up to 20 tonnes of materials per trip.

### Gross Weight - Loaded (t)
The **total weight of the fully loaded vehicle**, combining the vehicle's own tare weight and the cargo it carries. This is the weight the vehicle exerts on the road during a delivery trip.

> Gross Weight = Payload Capacity + Tare Weight

### Tare Weight / Empty Weight (t)
The unladen weight of the vehicle itself, with no cargo. Used to calculate the return-trip emissions when the vehicle travels back to the supplier after unloading.

> Empty Weight = Gross Weight − Payload Capacity

### Emission Factor (kgCO₂e / t·km)
The mass of greenhouse gas (expressed in CO₂ equivalent) emitted per tonne of cargo per kilometre travelled. It accounts for fuel consumption, vehicle size, and load characteristics.

---

## Reference Vehicle Classes

Indicative gross weight ranges and emission factors for common road freight classes:

| Vehicle Class | Gross Weight - Loaded | Emission Factor (kgCO₂e / t·km) |
|---|---|---|
| Light Duty Vehicle | < 4.5 t | 1.20 |
| HDV Small | 4.5 – 9 t | 0.70 |
| HDV Medium | 9 – 12 t | 0.55 |
| HDV Large | > 12 t | 0.19 |

> **HDV** = Heavy Duty Vehicle.
> Values are indicative defaults. Actual emission factors vary with fuel type, load factor, road conditions, and regional fleet data.

---

## How Trips Are Calculated

$$\text{Trips}_i = \left\lceil \frac{\text{Cargo}_i \text{ (kg)}}{\text{Payload Capacity (kg)}} \right\rceil$$

When **Pool same materials** is enabled, the same material used across multiple processes is combined into one shipment before the ceiling is applied.

## How Emissions Are Calculated

Every loaded trip incurs one empty return trip:

$$\text{Emission} = \text{Trips} \times \text{Distance (km)} \times \text{EF} \times (\text{Gross Weight} + \text{Empty Weight})$$

where **Empty Weight = Gross Weight − Payload Capacity**.
