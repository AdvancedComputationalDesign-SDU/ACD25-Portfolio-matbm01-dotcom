---
layout: default
title: Project Documentation
parent: "A1: NumPy Array Manipulation for 2D Pattern Generation"
nav_order: 2
nav_exclude: false
search_exclude: false
---

# Assignment 1: NumPy Array Manipulation for 2D Pattern Generation

[View on GitHub]({{ site.github.repository_url }})


![A1/images/layered_pattern.png<>](images/layered_pattern.png)

## Objective

The goal of this assignment is to create a Python program using NumPy to manipulate a 2-dimensional array and transform a blank canvas into a patterned image. You are asked apply various array operations, introduce randomness, and work with RGB channels to produce full-color images.

---

## Repository structure

```
A1/
├── index.md                    
├── README.md                   
├── BRIEF.md                    
├── pattern_generator.py
└── images/
    └── layered_pattern.png
```


## Table of Contents

- Pseudo-Code  
- Technical Explanation  
- Results  
- References  

---

## Pseudo-Code

1. Initialize parameters  
   - Define the image resolution using height = 200 and width = 200.

2. Create blank canvas  
   - Initialize a black RGB image using np.zeros((height, width, 3)).

3. Generate coordinate system  
   - Create X and Y grids using np.arange() and np.meshgrid().  
   - These grids define pixel positions and act as input domains for pattern generation.

4. Generate base sine-wave fields  
   - Apply sine functions to the coordinate grids.  
   - Use different frequencies and orientations for each color channel.

5. Create radial gradient field  
   - Compute the distance from each pixel to the image center.  
   - Normalize and invert distances to create a center-focused gradient.

6. Generate smooth noise field  
   - Create a random field using np.random.rand().  
   - Smooth the noise by averaging neighboring values using np.roll().

7. Combine pattern layers  
   - Modulate sine-wave fields with the radial gradient and noise.  
   - Blend the resulting fields into the RGB channels.

8. Draw central square frame  
   - Compute the square’s position and size relative to the image dimensions.  
   - Use NumPy slicing to draw a white square border.

9. Add random green squares  
   - Place several small green squares at random positions.  
   - Use random intensities to introduce local contrast.

10. Save and display result  
    - Save the final image to the images/ folder.  
    - Display the image using Matplotlib.

---

## Technical Explanation

The image is represented as a 3D NumPy array where each pixel contains red, green, and blue intensity values. A 
coordinate system is first generated using meshgrid, allowing pixel positions to be used as inputs to mathematical 
functions.

Sine functions are applied to the coordinate grids to create smooth, periodic base patterns. Each color channel uses 
a different frequency and orientation, preventing uniform repetition. A radial gradient is then introduced to 
establish a global spatial hierarchy by emphasizing the image center and fading toward the edges.

To avoid purely deterministic output, a spatially smoothed noise field is generated. This noise is blended with the 
sine-wave patterns, allowing randomness to influence the global structure of the image rather than acting only as a 
decorative overlay.

A central square frame is added through direct array slicing, creating contrast between rigid geometric structure and 
organic background patterns. Finally, randomly placed green squares introduce localized variation and scale contrast.

The resulting array is clipped to valid color ranges, saved as an image, and displayed using Matplotlib.

---

## Results

![A1/images/layered_pattern.png<>](images/layered_pattern.png)

The final image demonstrates layered NumPy-based manipulation. A sine-based RGB background 
is modulated by both a radial gradient and a smooth noise field, producing a coherent but 
non-uniform structure.

A white square frame provides geometric contrast, while smaller randomly placed green 
squares add localized variation. Because the noise field is regenerated each time the script runs, the overall visual 
structure remains consistent while subtle details change between executions.

---

## References

https://numpy.org/doc/stable/reference/generated/numpy.sin.html  
https://numpy.org/doc/stable/reference/generated/numpy.meshgrid.html  
https://numpy.org/doc/stable/reference/generated/numpy.random.rand.html  
