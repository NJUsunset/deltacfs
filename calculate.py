import constant
import modules
import grn_input
import cmp_input

if __name__ == '__main__':
    # Load the input data
    grn_input_data = grn_input.load_data()
    cmp_input_data = cmp_input.load_data()

    # Calculate the output
    output = modules.calculate(grn_input_data, cmp_input_data)

    # Save the output
    modules.save_output(output)