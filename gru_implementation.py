import json
import numpy as np
import sys

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def gru_forward(X, W_z, U_z, b_z, W_r, U_r, b_r, W_h, U_h, b_h):
    T, d = X.shape
    h = W_z.shape[0]
    
    H = np.zeros((T, h))
    h_prev = np.zeros(h)
    
    for t in range(T):
        x_t = X[t]
        
        z_t = sigmoid(W_z @ x_t + U_z @ h_prev + b_z)
        r_t = sigmoid(W_r @ x_t + U_r @ h_prev + b_r)
        h_tilde = np.tanh(W_h @ x_t + U_h @ (r_t * h_prev) + b_h)
        h_t = (1 - z_t) * h_prev + z_t * h_tilde
        
        H[t] = h_t
        h_prev = h_t
    
    flattened = H.flatten()
    return flattened

def main():
    try:
        input_text = sys.stdin.read().strip()
        
        if not input_text:
            print("[]")
            return
        
        input_data = json.loads(input_text)
        
        X = np.array(input_data['X'])
        W_z = np.array(input_data['W_z'])
        U_z = np.array(input_data['U_z'])
        b_z = np.array(input_data['b_z'])
        W_r = np.array(input_data['W_r'])
        U_r = np.array(input_data['U_r'])
        b_r = np.array(input_data['b_r'])
        W_h = np.array(input_data['W_h'])
        U_h = np.array(input_data['U_h'])
        b_h = np.array(input_data['b_h'])
        
        result = gru_forward(X, W_z, U_z, b_z, W_r, U_r, b_r, W_h, U_h, b_h)
        
        rounded_result = [round(x, 6) for x in result]
        
        print(json.dumps(rounded_result))
        
    except Exception as e:
        print("[]")

if __name__ == "__main__":
    main()
