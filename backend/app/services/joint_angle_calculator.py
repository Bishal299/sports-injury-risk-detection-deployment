import numpy as np


class JointAngleCalculator:
    """
    Calculates joint angles from MediaPipe landmarks.
    """

    @staticmethod
    def calculate_angle(a, b, c):
        """
        Calculate angle ABC in degrees.

        Parameters:
            a: First point  -> (x, y)
            b: Joint point  -> (x, y)
            c: Third point  -> (x, y)

        Returns:
            float: angle in degrees
            None: if the angle cannot be calculated
        """

        a = np.asarray(a, dtype=np.float64)
        b = np.asarray(b, dtype=np.float64)
        c = np.asarray(c, dtype=np.float64)

        # Vectors from joint B
        ba = a - b
        bc = c - b

        # Vector magnitudes
        norm_ba = np.linalg.norm(ba)
        norm_bc = np.linalg.norm(bc)

        # Prevent division by zero
        if norm_ba < 1e-8 or norm_bc < 1e-8:
            return None

        # Cosine of angle
        cosine = np.dot(ba, bc) / (
            norm_ba * norm_bc
        )

        # Protect against floating-point errors
        cosine = np.clip(
            cosine,
            -1.0,
            1.0
        )

        # Convert radians → degrees
        angle = np.degrees(
            np.arccos(cosine)
        )

        return float(angle)


if __name__ == "__main__":

    hip = (1, 2)
    knee = (2, 2)
    ankle = (3, 2)

    angle = JointAngleCalculator.calculate_angle(
        hip,
        knee,
        ankle
    )

    print("Knee Angle:", angle)