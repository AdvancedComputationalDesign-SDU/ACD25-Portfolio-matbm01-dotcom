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


## Table of Contents

- Pseudo-Code  
- Technical Explanation  
- Results  
- References  


## Pseudo-Code
1. Define image domain
   Set the resolution of the image to establish the spatial domain
   in which all patterns will be generated.

2. Initialize image field
   Create an empty RGB image that will be progressively built up
   through layered mathematical transformations.

3. Establish spatial reference system
   Generate a 2D coordinate grid representing pixel positions.
   This grid serves as the input space for all procedural patterns.

4. Generate periodic base structures
   Create multiple sine-based fields oriented along different axes.
   Each field represents a smooth, repeating structure assigned
   to a specific color channel.

5. Introduce global spatial hierarchy
   Compute a radial field centered in the image.
   Use this field to emphasize the center and gradually reduce
   intensity toward the edges.

6. Introduce controlled randomness
   Generate a continuous noise field by smoothing random values.
   This ensures variability while preserving spatial coherence.

7. Combine pattern layers
   Modulate the periodic base structures using the gradient and
   noise fields to produce a layered, non-uniform image.
   Blend the resulting fields into the RGB channels.

8. Add geometric contrast
   Overlay a rigid square frame at the center of the image.
   This introduces a clear contrast between organic and
   geometric structures.

9. Add localized variation
   Insert several small, randomly positioned color accents
   to create scale contrast and visual tension.

10. Output result
    Convert the computed image into a valid color format,
    save it to disk, and display it for inspection.

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
